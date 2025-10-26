"""
Security utilities and middleware for Value Architect Service
Implements security headers, rate limiting, and input validation
"""

import os
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimiter:
    """Redis-based rate limiter for API endpoints"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
    
    async def init(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def is_rate_limited(
        self,
        key: str,
        max_requests: int = 5,
        window_seconds: int = 60
    ) -> bool:
        """Check if request exceeds rate limit"""
        if not self.redis_client:
            return False
        
        current_count = await self.redis_client.incr(key)
        
        if current_count == 1:
            # First request in window, set expiration
            await self.redis_client.expire(key, window_seconds)
        
        return current_count > max_requests


class InputValidator:
    """Validate and sanitize user inputs"""
    
    # Regex patterns for validation
    PATTERNS = {
        'company_name': r'^[a-zA-Z0-9\s\-\.&\'()]+$',
        'industry': r'^[a-zA-Z\s]+$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    }
    
    # Field length limits
    LENGTH_LIMITS = {
        'company_name': 200,
        'industry': 100,
        'email': 254,
        'context': 10000,
        'description': 5000,
    }
    
    @staticmethod
    def validate_string(
        value: str,
        field_name: str,
        min_length: int = 1,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allow_empty: bool = False
    ) -> str:
        """Validate a string field"""
        if not value and allow_empty:
            return value
        
        if not value:
            raise ValueError(f"{field_name} is required")
        
        if len(value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters")
        
        max_len = max_length or InputValidator.LENGTH_LIMITS.get(field_name, 1000)
        if len(value) > max_len:
            raise ValueError(f"{field_name} must not exceed {max_len} characters")
        
        if pattern and not re.match(pattern, value):
            raise ValueError(f"{field_name} format is invalid")
        
        return value.strip()
    
    @staticmethod
    def validate_company_name(name: str) -> str:
        """Validate company name"""
        return InputValidator.validate_string(
            name,
            "company_name",
            min_length=1,
            max_length=200,
            pattern=InputValidator.PATTERNS['company_name']
        )
    
    @staticmethod
    def validate_industry(industry: str) -> str:
        """Validate industry field"""
        return InputValidator.validate_string(
            industry,
            "industry",
            min_length=1,
            max_length=100,
            pattern=InputValidator.PATTERNS['industry']
        )
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        return InputValidator.validate_string(
            email,
            "email",
            min_length=5,
            max_length=254,
            pattern=InputValidator.PATTERNS['email']
        )
    
    @staticmethod
    def validate_dict_size(data: Dict[str, Any], max_size: int = 10000) -> Dict[str, Any]:
        """Validate dictionary size"""
        import json
        size = len(json.dumps(data))
        if size > max_size:
            raise ValueError(f"Data exceeds maximum size of {max_size} bytes")
        return data


class PasswordValidator:
    """Validate password strength according to NIST 800-63B"""
    
    # Common passwords to reject
    COMMON_PASSWORDS = {
        'password', '123456', 'password123', 'admin', 'letmein',
        'welcome', 'monkey', '1234567890', 'qwerty', 'abc123'
    }
    
    @staticmethod
    def validate(password: str) -> bool:
        """
        Validate password strength according to NIST 800-63B
        Requirements:
        - Minimum 12 characters (14+ recommended)
        - Check against common password list
        - No sequential characters
        - No username/email in password
        """
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain lowercase letter")
        
        if not re.search(r'[0-9]', password):
            raise ValueError("Password must contain number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain special character")
        
        # Check against common passwords
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            raise ValueError("Password is too common")
        
        # Check for sequential characters
        if PasswordValidator._has_sequential_chars(password):
            raise ValueError("Password contains sequential characters")
        
        return True
    
    @staticmethod
    def _has_sequential_chars(password: str, length: int = 3) -> bool:
        """Check for sequential characters like 'abc' or '123'"""
        for i in range(len(password) - length + 1):
            substring = password[i:i + length]
            # Check if characters are sequential
            if all(ord(substring[j]) + 1 == ord(substring[j + 1]) 
                   for j in range(len(substring) - 1)):
                return True
        return False


async def rate_limit_check(
    request: Request,
    rate_limiter: RateLimiter,
    max_requests: int = 5,
    window_seconds: int = 60
):
    """Dependency for rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path
    key = f"rate_limit:{endpoint}:{client_ip}"
    
    if await rate_limiter.is_rate_limited(key, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
