"""
Security middleware and CORS configuration for ValueVerse Billing System
"""

import os
import time
import uuid
import asyncio
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import redis.asyncio as redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the application"""
    
    # Get allowed origins from environment
    allowed_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,https://billing.valueverse.com"
    ).split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    logger.info(f"CORS configured with origins: {allowed_origins}")

def configure_trusted_hosts(app: FastAPI) -> None:
    """Configure trusted host middleware"""
    
    allowed_hosts = os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,billing.valueverse.com,*.valueverse.com"
    ).split(",")
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    
    logger.info(f"Trusted hosts configured: {allowed_hosts}")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(self), usb=(), magnetometer=(), "
            "accelerometer=(), gyroscope=()"
        )
        
        # Content Security Policy
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com wss://billing.valueverse.com; "
                "frame-src https://js.stripe.com https://hooks.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )
            
            # Strict Transport Security (HSTS)
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        redis_url: Optional[str] = None,
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.redis_url = redis_url or os.getenv(
            "RATE_LIMIT_REDIS_URL",
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        )
        self.clients = {}
        self.redis_client: Optional[redis.Redis] = None
        self._redis_lock = asyncio.Lock()
        # expose instance for shutdown cleanup
        setattr(app.state, "rate_limit_middleware", self)

    async def _get_redis_client(self) -> Optional[redis.Redis]:
        if not self.redis_url:
            return None
        if self.redis_client:
            return self.redis_client
        async with self._redis_lock:
            if self.redis_client:
                return self.redis_client
            try:
                client = redis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
                await client.ping()
                self.redis_client = client
                logger.info("Rate limit middleware connected to Redis")
            except (RedisError, ConnectionError) as exc:
                logger.warning(
                    "Rate limit middleware failed to connect to Redis (%s); falling back to in-memory counters",
                    exc,
                )
                self.redis_client = None
            return self.redis_client

    async def close(self) -> None:
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.client:
            client_id = request.client.host
            now = time.time()
            redis_client = await self._get_redis_client()
            if redis_client:
                key = f"rate_limit:{client_id}:{request.url.path}"
                try:
                    current_count = await redis_client.incr(key)
                    if current_count == 1:
                        await redis_client.expire(key, self.period)
                    if current_count > self.calls:
                        retry_after = await redis_client.ttl(key)
                        retry_after = retry_after if retry_after and retry_after > 0 else self.period
                        return Response(
                            content="Rate limit exceeded",
                            status_code=429,
                            headers={
                                "X-RateLimit-Limit": str(self.calls),
                                "X-RateLimit-Remaining": "0",
                                "Retry-After": str(retry_after),
                            },
                        )
                    response = await call_next(request)
                    remaining = max(0, self.calls - current_count)
                    response.headers["X-RateLimit-Limit"] = str(self.calls)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    if remaining == 0:
                        ttl = await redis_client.ttl(key)
                        if ttl and ttl > 0:
                            response.headers["Retry-After"] = str(ttl)
                    return response
                except RedisError as exc:
                    logger.error("Redis rate limiting error: %s", exc)
                    # fall back to in-memory counters below
            
            # Clean old entries
            self.clients = {
                k: v for k, v in self.clients.items()
                if now - v["first_request"] < self.period
            }
            
            if client_id in self.clients:
                client_data = self.clients[client_id]
                if now - client_data["first_request"] < self.period:
                    if client_data["request_count"] >= self.calls:
                        response = Response(
                            content="Rate limit exceeded",
                            status_code=429,
                            headers={
                                "X-RateLimit-Limit": str(self.calls),
                                "X-RateLimit-Remaining": "0",
                                "Retry-After": str(self.period)
                            }
                        )
                        return response
                    client_data["request_count"] += 1
                else:
                    self.clients[client_id] = {
                        "first_request": now,
                        "request_count": 1
                    }
            else:
                self.clients[client_id] = {
                    "first_request": now,
                    "request_count": 1
                }
            
            response = await call_next(request)
            
            # Add rate limit headers
            if client_id in self.clients:
                remaining = self.calls - self.clients[client_id]["request_count"]
                response.headers["X-RateLimit-Limit"] = str(self.calls)
                response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
                if remaining <= 0:
                    reset = self.period - (now - self.clients[client_id]["first_request"])
                    response.headers["Retry-After"] = str(max(0, int(reset)))
            
            return response
        
        return await call_next(request)

def configure_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application"""
    
    # Configure CORS first
    configure_cors(app)
    
    # Configure trusted hosts
    configure_trusted_hosts(app)
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request ID tracking
    app.add_middleware(RequestIDMiddleware)
    
    # Add logging
    app.add_middleware(LoggingMiddleware)
    
    # Add rate limiting in production
    if os.getenv("ENVIRONMENT") == "production":
        rate_limit_kwargs = {
            "calls": int(os.getenv("RATE_LIMIT_CALLS", "100")),
            "period": int(os.getenv("RATE_LIMIT_PERIOD", "60")),
            "redis_url": os.getenv("RATE_LIMIT_REDIS_URL"),
        }
        app.add_middleware(RateLimitMiddleware, **rate_limit_kwargs)
        
        @app.on_event("shutdown")
        async def _shutdown_rate_limit() -> None:
            middleware_instance = getattr(app.state, "rate_limit_middleware", None)
            if middleware_instance:
                await middleware_instance.close()
    
    logger.info("All middleware configured successfully")
