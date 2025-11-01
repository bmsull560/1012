"""
Unit tests for authentication and authorization module
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
import os


class FakeRedisClient:
    """Minimal async Redis replacement for unit tests."""

    def __init__(self):
        self._values: dict[str, int] = {}
        self._expirations: dict[str, datetime] = {}

    async def incr(self, key: str) -> int:
        self._purge_expired(key)
        new_value = self._values.get(key, 0) + 1
        self._values[key] = new_value
        return new_value

    async def expire(self, key: str, seconds: int) -> None:
        self._expirations[key] = datetime.utcnow() + timedelta(seconds=seconds)

    async def close(self) -> None:
        self._values.clear()
        self._expirations.clear()

    def _purge_expired(self, key: str) -> None:
        expiration = self._expirations.get(key)
        if expiration and expiration <= datetime.utcnow():
            self._values.pop(key, None)
            self._expirations.pop(key, None)

from backend.auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    verify_token, RateLimiter,
    TokenData, SECRET_KEY, ALGORITHM
)

class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification works correctly"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
    
    def test_unique_hashes(self):
        """Test that same password produces different hashes"""
        password = "TestPassword456"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

class TestTokenGeneration:
    """Test JWT token generation and verification"""
    
    @pytest.mark.asyncio
    async def test_access_token_creation(self):
        """Test access token creation"""
        data = {
            "organization_id": str(uuid4()),
            "user_id": str(uuid4()),
            "email": "user@example.com",
            "scopes": ["read", "write"]
        }
        
        token = create_access_token(data, timedelta(minutes=15))
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["organization_id"] == data["organization_id"]
        assert decoded["user_id"] == data["user_id"]
        assert decoded["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_refresh_token_creation(self):
        """Test refresh token creation"""
        data = {
            "organization_id": str(uuid4()),
            "user_id": str(uuid4())
        }
        
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["organization_id"] == data["organization_id"]
        assert decoded["type"] == "refresh"
    
    @pytest.mark.asyncio
    async def test_token_verification_success(self):
        """Test successful token verification"""
        org_id = str(uuid4())
        user_id = str(uuid4())
        
        token = create_access_token({
            "organization_id": org_id,
            "user_id": user_id,
            "email": "admin@example.com",
            "scopes": ["admin"]
        })
        
        token_data = await verify_token(token, "access")
        
        assert token_data.organization_id == org_id
        assert token_data.user_id == user_id
        assert "admin" in token_data.scopes
    
    @pytest.mark.asyncio
    async def test_token_verification_wrong_type(self):
        """Test token verification fails with wrong type"""
        token = create_refresh_token({
            "organization_id": str(uuid4()),
            "user_id": str(uuid4())
        })
        
        with pytest.raises(Exception):
            await verify_token(token, "access")  # Expecting access, got refresh
    
    @pytest.mark.asyncio
    async def test_expired_token(self):
        """Test expired token verification fails"""
        token = create_access_token(
            {
                "organization_id": str(uuid4()),
                "user_id": str(uuid4()),
                "email": "expired@example.com",
            },
            timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(Exception):
            await verify_token(token, "access")

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests within limit"""
        limiter = RateLimiter(
            max_requests=5,
            window_seconds=60,
            redis_client=FakeRedisClient(),
        )
        
        key = "test_user_1"
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed = await limiter.check_rate_limit(key)
            assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_excess_requests(self):
        """Test rate limiter blocks requests over limit"""
        limiter = RateLimiter(
            max_requests=3,
            window_seconds=60,
            redis_client=FakeRedisClient(),
        )
        
        key = "test_user_2"
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed = await limiter.check_rate_limit(key)
            assert allowed is True
        
        # 4th request should be blocked
        allowed = await limiter.check_rate_limit(key)
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_window(self):
        """Test rate limiter resets after time window"""
        limiter = RateLimiter(
            max_requests=2,
            window_seconds=1,
            redis_client=FakeRedisClient(),
        )
        
        key = "test_user_3"
        
        # Use up the limit
        assert await limiter.check_rate_limit(key) is True
        assert await limiter.check_rate_limit(key) is True
        assert await limiter.check_rate_limit(key) is False
        
        # Wait for window to expire
        import asyncio
        await asyncio.sleep(1.1)
        
        # Should be allowed again
        assert await limiter.check_rate_limit(key) is True

    @pytest.mark.asyncio
    async def test_rate_limiter_falls_back_to_memory_on_errors(self):
        """Redis failures should not break rate limiting enforcement."""

        class FailingRedis:
            async def incr(self, key: str) -> int:
                raise ConnectionError("redis unavailable")

            async def expire(self, key: str, seconds: int) -> None:
                return None

            async def close(self) -> None:
                return None

        limiter = RateLimiter(
            max_requests=1,
            window_seconds=60,
            redis_client=FailingRedis(),
        )

        key = "fallback_user"

        assert await limiter.check_rate_limit(key) is True
        assert await limiter.check_rate_limit(key) is False
