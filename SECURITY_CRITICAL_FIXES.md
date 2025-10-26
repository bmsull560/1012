# Critical Security Fixes - Implementation Guide

## Overview

This document provides step-by-step implementation guidance for the 4 CRITICAL security issues identified in the security audit.

---

## Fix #1: Real User Authentication

### Current Code (INSECURE)
```python
# backend/auth.py:125-132
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
```

### Required Changes

#### Step 1: Create User Model
Add to `backend/models.py`:

```python
class User(Base):
    """User authentication and authorization model"""
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    organization_id = Column(PostgresUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Status and permissions
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    
    # Metadata
    scopes = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="users")
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_organization", "organization_id"),
        CheckConstraint("failed_login_attempts >= 0", name="check_failed_attempts"),
    )
```

#### Step 2: Create Database Migration
```bash
cd billing-system/backend
alembic revision -m "add_users_table"
```

Edit the migration file:
```python
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('scopes', postgresql.JSONB(), default=list),
        sa.Column('metadata', postgresql.JSONB(), default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_organization', 'users', ['organization_id'])

def downgrade():
    op.drop_index('idx_users_organization')
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

#### Step 3: Fix get_current_user Function
Replace in `backend/auth.py`:

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AuthUser:
    """Get the current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    token_data = await verify_token(token, token_type="access")
    
    if not token_data.user_id:
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == UUID(token_data.user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {user.locked_until.isoformat()}"
        )
    
    # Verify organization matches token
    if str(user.organization_id) != token_data.organization_id:
        raise credentials_exception
    
    # Return authenticated user
    return AuthUser(
        id=user.id,
        email=user.email,
        organization_id=user.organization_id,
        is_active=user.is_active,
        is_admin=user.is_admin
    )
```

#### Step 4: Add User Import
Add to imports in `backend/auth.py`:
```python
from .models import Organization, User
```

---

## Fix #2: Redis-Based Rate Limiting

### Current Code (INSECURE)
```python
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # In-memory - PROBLEM!
```

### Required Changes

#### Step 1: Install Redis Client
Already in `requirements.txt`:
```
redis==5.0.1
```

#### Step 2: Create Redis Rate Limiter
Replace `RateLimiter` class in `backend/auth.py`:

```python
import redis.asyncio as redis
from datetime import datetime, timedelta

class RedisRateLimiter:
    """Redis-based distributed rate limiter"""
    
    def __init__(
        self, 
        redis_url: str = None,
        max_requests: int = 100, 
        window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None
    
    async def _get_redis(self):
        """Lazy initialization of Redis connection"""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    async def check_rate_limit(self, key: str) -> bool:
        """
        Check if rate limit is exceeded using sliding window algorithm
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        redis_client = await self._get_redis()
        
        # Use Redis sorted set for sliding window
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds
        
        # Key for this rate limit bucket
        bucket_key = f"rate_limit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(bucket_key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(bucket_key)
        
        # Add current request
        pipe.zadd(bucket_key, {str(now): now})
        
        # Set expiry on the key
        pipe.expire(bucket_key, self.window_seconds + 1)
        
        # Execute pipeline
        results = await pipe.execute()
        
        # results[1] is the count before adding current request
        request_count = results[1]
        
        # Check if limit exceeded
        if request_count >= self.max_requests:
            # Remove the request we just added since it's rejected
            await redis_client.zrem(bucket_key, str(now))
            return False
        
        return True
    
    async def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window"""
        redis_client = await self._get_redis()
        
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds
        bucket_key = f"rate_limit:{key}"
        
        # Clean old entries and count
        await redis_client.zremrangebyscore(bucket_key, 0, window_start)
        count = await redis_client.zcard(bucket_key)
        
        return max(0, self.max_requests - count)
    
    async def reset(self, key: str):
        """Reset rate limit for a key"""
        redis_client = await self._get_redis()
        bucket_key = f"rate_limit:{key}"
        await redis_client.delete(bucket_key)
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()

# Create global instance
rate_limiter = RedisRateLimiter()
```

#### Step 3: Update Rate Limit Dependency
Replace in `backend/auth.py`:

```python
async def check_rate_limit(
    current_user: AuthUser = Depends(get_current_user)
) -> None:
    """Check rate limit for current user"""
    key = f"user:{current_user.id}"
    
    if not await rate_limiter.check_rate_limit(key):
        remaining = await rate_limiter.get_remaining(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(rate_limiter.window_seconds)
            }
        )
```

---

## Fix #3: Secure Key Management

### Current Code (INSECURE)
```python
def __init__(self, master_key: Optional[str] = None):
    self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
    if not self.master_key:
        # Generate a key for development (use KMS in production)
        self.master_key = Fernet.generate_key().decode()
        logger.warning("Generated development encryption key")
```

### Required Changes

#### Step 1: Add Startup Validation
Create `backend/config.py`:

```python
"""
Configuration and environment validation
"""
import os
import sys
from typing import Optional

class SecurityConfig:
    """Security configuration with validation"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.encryption_master_key = os.getenv("ENCRYPTION_MASTER_KEY")
        self.redis_url = os.getenv("REDIS_URL")
        self.database_url = os.getenv("DATABASE_URL")
        
        # Validate critical settings
        self._validate()
    
    def _validate(self):
        """Validate critical security settings"""
        errors = []
        
        # JWT Secret Key
        if not self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY environment variable is required")
        elif self.jwt_secret_key == "your-secret-key-change-this-in-production":
            errors.append("JWT_SECRET_KEY must be changed from default value")
        elif len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters")
        
        # Encryption Key
        if self.environment == "production":
            if not self.encryption_master_key:
                errors.append("ENCRYPTION_MASTER_KEY is required in production")
            elif len(self.encryption_master_key) < 32:
                errors.append("ENCRYPTION_MASTER_KEY must be at least 32 characters")
        
        # Redis URL
        if not self.redis_url:
            errors.append("REDIS_URL environment variable is required")
        
        # Database URL
        if not self.database_url:
            errors.append("DATABASE_URL environment variable is required")
        
        # Fail fast if critical errors
        if errors:
            print("CRITICAL SECURITY CONFIGURATION ERRORS:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            print("\nApplication cannot start with these security issues.", file=sys.stderr)
            sys.exit(1)
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

# Global config instance
config = SecurityConfig()
```

#### Step 2: Update EncryptionManager
Replace in `backend/database_security.py`:

```python
from .config import config

class EncryptionManager:
    """
    Manages field-level encryption for sensitive data
    """
    
    def __init__(self, master_key: Optional[str] = None):
        # Use provided key or config
        self.master_key = master_key or config.encryption_master_key
        
        # In development, allow key generation with warning
        if not self.master_key:
            if config.is_production():
                raise RuntimeError(
                    "ENCRYPTION_MASTER_KEY is required in production. "
                    "Application cannot start without encryption key."
                )
            else:
                self.master_key = Fernet.generate_key().decode()
                logger.warning(
                    "⚠️  DEVELOPMENT MODE: Generated temporary encryption key. "
                    "Data encrypted with this key will be lost on restart. "
                    "Set ENCRYPTION_MASTER_KEY environment variable for persistence."
                )
        
        # Validate key format
        try:
            self.fernet = Fernet(
                self.master_key.encode() if isinstance(self.master_key, str) else self.master_key
            )
        except Exception as e:
            raise RuntimeError(f"Invalid encryption key format: {e}")
    
    # ... rest of the class remains the same
```

#### Step 3: Add Key Rotation Support
Add to `EncryptionManager`:

```python
def __init__(self, master_key: Optional[str] = None, old_keys: Optional[List[str]] = None):
    """
    Initialize with support for key rotation
    
    Args:
        master_key: Current encryption key
        old_keys: List of previous keys for decryption during rotation
    """
    self.master_key = master_key or config.encryption_master_key
    self.old_keys = old_keys or []
    
    # ... validation code ...
    
    # Create Fernet instances for all keys
    self.fernet = Fernet(self.master_key.encode())
    self.old_fernets = [Fernet(key.encode()) for key in self.old_keys]

def decrypt(self, encrypted_data: bytes) -> str:
    """Decrypt with support for old keys during rotation"""
    if not encrypted_data:
        return None
    
    # Try current key first
    try:
        return self.fernet.decrypt(encrypted_data).decode()
    except Exception:
        pass
    
    # Try old keys
    for old_fernet in self.old_fernets:
        try:
            return old_fernet.decrypt(encrypted_data).decode()
        except Exception:
            continue
    
    # If all keys fail, raise error
    raise ValueError("Unable to decrypt data with any available key")
```

#### Step 4: Environment Variable Documentation
Create `.env.example.secure`:

```bash
# Security Configuration - REQUIRED FOR PRODUCTION

# JWT Secret Key (REQUIRED)
# Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# Encryption Master Key (REQUIRED IN PRODUCTION)
# Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
ENCRYPTION_MASTER_KEY=

# Old encryption keys for rotation (comma-separated)
ENCRYPTION_OLD_KEYS=

# Redis URL (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# Database URL (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/billing

# Environment
ENVIRONMENT=production
```

---

## Fix #4: Compliance Framework

### Step 1: Create Sensitive Field Registry
Create `backend/compliance.py`:

```python
"""
Compliance and data protection utilities
"""
from typing import Dict, List, Set, Any
from enum import Enum

class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # PCI, PHI, PII

class SensitiveFieldRegistry:
    """
    Centralized registry of sensitive fields for compliance
    """
    
    # PCI DSS - Payment Card Industry
    PCI_FIELDS = {
        'card_number', 'cvv', 'cvv2', 'cvc', 'cvc2',
        'card_verification_value', 'card_security_code',
        'magnetic_stripe_data', 'track_data', 'pin', 'pin_block'
    }
    
    # PII - Personally Identifiable Information (GDPR)
    PII_FIELDS = {
        'ssn', 'social_security_number', 'national_id',
        'passport_number', 'drivers_license', 'tax_id',
        'date_of_birth', 'birth_date'
    }
    
    # Financial Information
    FINANCIAL_FIELDS = {
        'account_number', 'routing_number', 'iban',
        'swift_code', 'bank_account', 'crypto_wallet'
    }
    
    # Authentication Credentials
    AUTH_FIELDS = {
        'password', 'password_hash', 'api_key', 'secret_key',
        'private_key', 'access_token', 'refresh_token'
    }
    
    @classmethod
    def get_all_sensitive_fields(cls) -> Set[str]:
        """Get all registered sensitive fields"""
        return (
            cls.PCI_FIELDS | 
            cls.PII_FIELDS | 
            cls.FINANCIAL_FIELDS | 
            cls.AUTH_FIELDS
        )
    
    @classmethod
    def classify_field(cls, field_name: str) -> DataClassification:
        """Classify a field by sensitivity"""
        field_lower = field_name.lower()
        
        if field_lower in cls.PCI_FIELDS:
            return DataClassification.RESTRICTED
        elif field_lower in cls.PII_FIELDS:
            return DataClassification.RESTRICTED
        elif field_lower in cls.FINANCIAL_FIELDS:
            return DataClassification.CONFIDENTIAL
        elif field_lower in cls.AUTH_FIELDS:
            return DataClassification.CONFIDENTIAL
        else:
            return DataClassification.INTERNAL
    
    @classmethod
    def should_encrypt(cls, field_name: str) -> bool:
        """Determine if field should be encrypted at rest"""
        return field_name.lower() in cls.get_all_sensitive_fields()
    
    @classmethod
    def should_mask_in_logs(cls, field_name: str) -> bool:
        """Determine if field should be masked in logs"""
        return field_name.lower() in cls.get_all_sensitive_fields()
    
    @classmethod
    def get_retention_period_days(cls, field_name: str) -> int:
        """Get data retention period for GDPR compliance"""
        classification = cls.classify_field(field_name)
        
        if classification == DataClassification.RESTRICTED:
            return 90  # 3 months for PCI/PII
        elif classification == DataClassification.CONFIDENTIAL:
            return 365  # 1 year for financial
        else:
            return 730  # 2 years for internal
```

### Step 2: Update Audit Logger
Replace `_mask_sensitive_data` in `backend/database_security.py`:

```python
from .compliance import SensitiveFieldRegistry

def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in data using registry"""
    if not data:
        return data
    
    masked = data.copy()
    
    for field, value in masked.items():
        if SensitiveFieldRegistry.should_mask_in_logs(field):
            if value:
                # Keep last 4 characters for reference
                str_value = str(value)
                if len(str_value) > 4:
                    masked[field] = '*' * (len(str_value) - 4) + str_value[-4:]
                else:
                    masked[field] = '****'
    
    return masked
```

---

## Testing the Fixes

### Test #1: User Authentication
```python
# tests/unit/test_auth_fixed.py
import pytest
from backend.auth import get_current_user
from backend.models import User

@pytest.mark.asyncio
async def test_get_current_user_real_lookup(test_db, test_organization):
    """Test that get_current_user performs real database lookup"""
    # Create real user
    user = User(
        email="test@example.com",
        password_hash="hashed",
        organization_id=test_organization.id,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    
    # Create token
    token = create_access_token({
        "user_id": str(user.id),
        "organization_id": str(test_organization.id)
    })
    
    # Should fetch real user
    auth_user = await get_current_user(token, test_db)
    assert auth_user.email == "test@example.com"
    assert auth_user.id == user.id
```

### Test #2: Redis Rate Limiting
```python
@pytest.mark.asyncio
async def test_redis_rate_limiter_distributed():
    """Test Redis rate limiter works across instances"""
    limiter1 = RedisRateLimiter(max_requests=3, window_seconds=60)
    limiter2 = RedisRateLimiter(max_requests=3, window_seconds=60)
    
    key = "test_user"
    
    # Use up limit on instance 1
    assert await limiter1.check_rate_limit(key) is True
    assert await limiter1.check_rate_limit(key) is True
    assert await limiter1.check_rate_limit(key) is True
    
    # Instance 2 should see the same limit
    assert await limiter2.check_rate_limit(key) is False
```

### Test #3: Key Validation
```python
def test_encryption_manager_requires_key_in_production(monkeypatch):
    """Test that production requires encryption key"""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ENCRYPTION_MASTER_KEY", raising=False)
    
    with pytest.raises(RuntimeError, match="required in production"):
        EncryptionManager()
```

---

## Deployment Checklist

Before deploying these fixes:

- [ ] Run all existing tests
- [ ] Run new security tests
- [ ] Update environment variables in production
- [ ] Create database backup
- [ ] Run database migrations
- [ ] Test rate limiting with load testing
- [ ] Verify encryption/decryption works
- [ ] Test user authentication flow
- [ ] Update deployment documentation
- [ ] Schedule security review

---

## Rollback Plan

If issues occur:

1. **Database**: Revert migration with `alembic downgrade -1`
2. **Code**: Revert to previous git commit
3. **Environment**: Restore previous environment variables
4. **Redis**: Clear rate limit keys with `FLUSHDB`

---

**Last Updated:** 2025-10-26
**Reviewed By:** Security Team
**Approved By:** [Pending]
