"""
Authentication and authorization module for ValueVerse Billing System
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models import Organization

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production":
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable must be set to a secure, "
        "non-default value. This is required for production security. "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced from 30 for better security
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenData(BaseModel):
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list[str] = []

class AuthUser(BaseModel):
    id: UUID
    email: str
    organization_id: UUID
    is_active: bool = True
    is_admin: bool = False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != token_type:
            raise credentials_exception
            
        organization_id: str = payload.get("organization_id")
        user_id: str = payload.get("user_id")
        scopes: list = payload.get("scopes", [])
        
        if organization_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            organization_id=organization_id,
            user_id=user_id,
            scopes=scopes
        )
        return token_data
        
    except JWTError:
        raise credentials_exception

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AuthUser:
    """Get the current authenticated user from token"""
    token_data = await verify_token(token, token_type="access")
    
    # In a real application, fetch user from database
    # For now, return a mock user
    user = AuthUser(
        id=UUID(token_data.user_id) if token_data.user_id else UUID("00000000-0000-0000-0000-000000000000"),
        email="user@example.com",
        organization_id=UUID(token_data.organization_id),
        is_active=True,
        is_admin="admin" in token_data.scopes
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_organization(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Get the current user's organization"""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if organization.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is not active"
        )
    
    return organization

def require_scopes(*required_scopes: str):
    """Dependency to require specific scopes"""
    async def scope_checker(
        current_user: AuthUser = Depends(get_current_user)
    ):
        # In a real application, check user's actual scopes
        # For now, just check if user is admin for admin scopes
        for scope in required_scopes:
            if scope == "admin" and not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}"
                )
        return current_user
    return scope_checker

# Rate limiting decorator
import logging
from functools import wraps
from collections import defaultdict
from datetime import datetime
import asyncio

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - redis is optional for local dev
    redis = None

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        *,
        redis_client: Optional[Any] = None,
        redis_url: Optional[str] = None,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis_client: Optional[Any] = redis_client
        self._redis_url = redis_url or os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL")
        self._redis_lock = asyncio.Lock()
        self._memory_lock = asyncio.Lock()
        self._use_local_fallback = False

        if self._redis_client is None and redis is None:
            self._use_local_fallback = True
        elif self._redis_client is None and not self._redis_url:
            self._use_local_fallback = True
        self.requests = defaultdict(list)

    async def _initialize_redis_client(self) -> Optional[Any]:
        if self._redis_client is not None:
            return self._redis_client

        if self._use_local_fallback:
            return None

        if redis is None:
            self._use_local_fallback = True
            return None

        if not self._redis_url:
            self._use_local_fallback = True
            return None

        async with self._redis_lock:
            if self._redis_client is not None or self._use_local_fallback:
                return self._redis_client

            try:
                # Attempt to create a shared Redis client for distributed rate limiting
                self._redis_client = await redis.from_url(
                    self._redis_url,
                    decode_responses=True,
                )
            except Exception as exc:  # pragma: no cover - network failures
                logger.warning(
                    "Failed to initialize Redis for rate limiting. Falling back to in-memory storage: %s",
                    exc,
                )
                self._use_local_fallback = True
                self._redis_url = None

        return self._redis_client

    async def _close_redis(self) -> None:
        if self._redis_client is None:
            return

        try:
            await self._redis_client.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass
        finally:
            self._redis_client = None
            self._use_local_fallback = True
            self._redis_url = None

    async def _check_in_memory(self, key: str) -> bool:
        now = datetime.utcnow()
        minute_ago = now - timedelta(seconds=self.window_seconds)

        async with self._memory_lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > minute_ago
            ]

            if len(self.requests[key]) >= self.max_requests:
                return False

            self.requests[key].append(now)
            return True

    async def check_rate_limit(self, key: str) -> bool:
        """Check if rate limit is exceeded"""
        client = await self._initialize_redis_client()

        if client is not None and not self._use_local_fallback:
            try:
                current_count = await client.incr(key)

                if current_count == 1:
                    # First request in the window, set expiration
                    await client.expire(key, self.window_seconds)

                if current_count > self.max_requests:
                    return False

                return True
            except Exception as exc:  # pragma: no cover - operational fallback
                logger.warning(
                    "Redis rate limiting failed for key %s. Falling back to in-memory storage: %s",
                    key,
                    exc,
                )
                await self._close_redis()

        return await self._check_in_memory(key)

rate_limiter = RateLimiter()

async def check_rate_limit(
    current_user: AuthUser = Depends(get_current_user)
) -> None:
    """Check rate limit for current user"""
    key = f"user:{current_user.id}"
    
    if not await rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
