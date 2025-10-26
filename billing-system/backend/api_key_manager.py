"""
API Key Management System
Handles API key generation, validation, rotation, and rate limiting
"""

import os
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import redis.asyncio as redis
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel, Field, validator
from enum import Enum
import json


class APIKeyScope(str, Enum):
    """API key scopes/permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    
    # Service-specific scopes
    VALUE_MODEL_READ = "value_model:read"
    VALUE_MODEL_WRITE = "value_model:write"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    TENANT_ADMIN = "tenant:admin"


class APIKeyConfig(BaseModel):
    """Configuration for API key management"""
    key_prefix: str = Field(default="vv_", min_length=2, max_length=10)
    key_length: int = Field(default=32, ge=24, le=64)
    hash_algorithm: str = Field(default="sha256", pattern="^(sha256|sha512)$")
    
    max_keys_per_user: int = Field(default=10, ge=1, le=50)
    max_keys_per_tenant: int = Field(default=50, ge=1, le=200)
    
    default_expiry_days: int = Field(default=90, ge=30, le=365)
    max_expiry_days: int = Field(default=365, ge=90, le=730)
    
    rotation_warning_days: int = Field(default=14, ge=7, le=30)
    auto_rotate: bool = False
    
    rate_limit_enabled: bool = True
    default_rate_limit: int = Field(default=1000, ge=100, le=10000)
    rate_limit_window_seconds: int = Field(default=3600, ge=60, le=86400)
    
    audit_enabled: bool = True
    track_last_used: bool = True
    track_ip_addresses: bool = True


class APIKey(BaseModel):
    """API key model"""
    key_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    user_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    key_hash: str  # Hashed API key
    key_prefix: str  # First few characters for identification
    
    scopes: List[APIKeyScope] = Field(default_factory=list)
    
    rate_limit: Optional[int] = None
    rate_limit_window: Optional[int] = None
    
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_rotated_at: Optional[datetime] = None
    
    is_active: bool = True
    is_service_key: bool = False  # For service-to-service communication
    
    metadata: Optional[Dict[str, Any]] = None
    
    # Audit fields
    created_by: str
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoke_reason: Optional[str] = None


class APIKeyUsage(BaseModel):
    """API key usage tracking"""
    key_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    endpoint: str
    method: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    response_status: int
    response_time_ms: int
    
    
class APIKeyManager:
    """
    API Key Management System
    Handles generation, validation, rotation, and rate limiting
    """
    
    def __init__(
        self,
        redis_url: str,
        config: Optional[APIKeyConfig] = None
    ):
        """Initialize API key manager"""
        self.redis_url = redis_url
        self.config = config or APIKeyConfig()
        self.redis_client: Optional[redis.Redis] = None
    
    async def init(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def create_api_key(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        scopes: Optional[List[APIKeyScope]] = None,
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        is_service_key: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID creating the key
            name: Name for the API key
            description: Optional description
            scopes: List of permissions
            expires_in_days: Days until expiration
            rate_limit: Custom rate limit
            allowed_ips: IP whitelist
            allowed_origins: Origin whitelist
            is_service_key: Whether this is for service-to-service auth
            metadata: Additional metadata
        
        Returns:
            Dictionary with key details and the actual key (shown only once)
        """
        # Check limits
        await self._check_key_limits(tenant_id, user_id)
        
        # Generate API key
        raw_key = self._generate_api_key()
        key_hash = self._hash_key(raw_key)
        key_prefix = raw_key[:8]  # First 8 chars for identification
        
        # Calculate expiration
        if expires_in_days:
            expires_in_days = min(expires_in_days, self.config.max_expiry_days)
        else:
            expires_in_days = self.config.default_expiry_days
        
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key object
        api_key = APIKey(
            tenant_id=tenant_id,
            user_id=user_id if not is_service_key else None,
            name=name,
            description=description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes or [APIKeyScope.READ],
            rate_limit=rate_limit or self.config.default_rate_limit,
            rate_limit_window=self.config.rate_limit_window_seconds,
            allowed_ips=allowed_ips,
            allowed_origins=allowed_origins,
            expires_at=expires_at,
            is_service_key=is_service_key,
            metadata=metadata,
            created_by=user_id
        )
        
        # Store API key
        await self._store_api_key(api_key)
        
        # Track for tenant and user
        await self._track_api_key(tenant_id, user_id, api_key.key_id)
        
        # Log creation
        if self.config.audit_enabled:
            await self._audit_log(
                "api_key_created",
                {
                    "key_id": api_key.key_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "name": name,
                    "scopes": scopes
                }
            )
        
        return {
            "key_id": api_key.key_id,
            "api_key": raw_key,  # Only returned once!
            "name": name,
            "prefix": key_prefix,
            "scopes": api_key.scopes,
            "expires_at": expires_at.isoformat(),
            "rate_limit": api_key.rate_limit,
            "message": "Store this API key securely. It will not be shown again."
        }
    
    async def validate_api_key(
        self,
        api_key: str,
        required_scopes: Optional[List[APIKeyScope]] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Validate an API key and check permissions
        
        Args:
            api_key: The API key to validate
            required_scopes: Required scopes for the operation
            request: FastAPI request for IP/origin validation
        
        Returns:
            API key details if valid
        
        Raises:
            HTTPException: If key is invalid or lacks permissions
        """
        # Hash the provided key
        key_hash = self._hash_key(api_key)
        
        # Look up key by hash
        key_data = await self._get_api_key_by_hash(key_hash)
        
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check if active
        if not key_data.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked"
            )
        
        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at:
            expires_at = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )
        
        # Check IP whitelist
        if request and key_data.get("allowed_ips"):
            client_ip = request.client.host if request.client else None
            if client_ip and client_ip not in key_data.get("allowed_ips"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not allowed"
                )
        
        # Check origin whitelist
        if request and key_data.get("allowed_origins"):
            origin = request.headers.get("Origin")
            if origin and origin not in key_data.get("allowed_origins"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Origin not allowed"
                )
        
        # Check scopes
        if required_scopes:
            key_scopes = set(key_data.get("scopes", []))
            required = set(required_scopes)
            
            # Check for admin scope (grants all permissions)
            if APIKeyScope.ADMIN not in key_scopes:
                if not required.issubset(key_scopes):
                    missing = required - key_scopes
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Missing scopes: {missing}"
                    )
        
        # Check rate limit
        if self.config.rate_limit_enabled:
            key_id = key_data.get("key_id")
            rate_limit = key_data.get("rate_limit", self.config.default_rate_limit)
            window = key_data.get("rate_limit_window", self.config.rate_limit_window_seconds)
            
            if not await self._check_rate_limit(key_id, rate_limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
        
        # Update last used
        if self.config.track_last_used:
            await self._update_last_used(key_data.get("key_id"), request)
        
        # Check if rotation is needed
        if self._needs_rotation(key_data):
            key_data["rotation_warning"] = True
            key_data["rotate_by"] = (
                datetime.fromisoformat(key_data.get("expires_at")) - 
                timedelta(days=self.config.rotation_warning_days)
            ).isoformat()
        
        return {
            "key_id": key_data.get("key_id"),
            "tenant_id": key_data.get("tenant_id"),
            "user_id": key_data.get("user_id"),
            "scopes": key_data.get("scopes"),
            "is_service_key": key_data.get("is_service_key", False),
            "metadata": key_data.get("metadata"),
            "rotation_warning": key_data.get("rotation_warning", False)
        }
    
    async def rotate_api_key(
        self,
        key_id: str,
        user_id: str,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rotate an API key (create new, revoke old)
        
        Args:
            key_id: ID of key to rotate
            user_id: User performing rotation
            expires_in_days: New expiration period
        
        Returns:
            New API key details
        """
        # Get existing key
        old_key = await self._get_api_key(key_id)
        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Create new key with same settings
        new_key_result = await self.create_api_key(
            tenant_id=old_key.get("tenant_id"),
            user_id=user_id,
            name=f"{old_key.get('name')} (Rotated)",
            description=f"Rotated from {key_id}",
            scopes=old_key.get("scopes"),
            expires_in_days=expires_in_days,
            rate_limit=old_key.get("rate_limit"),
            allowed_ips=old_key.get("allowed_ips"),
            allowed_origins=old_key.get("allowed_origins"),
            is_service_key=old_key.get("is_service_key", False),
            metadata={
                **old_key.get("metadata", {}),
                "rotated_from": key_id,
                "rotated_at": datetime.utcnow().isoformat()
            }
        )
        
        # Revoke old key (with grace period)
        await self.revoke_api_key(
            key_id,
            user_id,
            reason=f"Rotated to {new_key_result['key_id']}",
            grace_period_minutes=60  # 1 hour grace period
        )
        
        # Log rotation
        if self.config.audit_enabled:
            await self._audit_log(
                "api_key_rotated",
                {
                    "old_key_id": key_id,
                    "new_key_id": new_key_result["key_id"],
                    "user_id": user_id
                }
            )
        
        return new_key_result
    
    async def revoke_api_key(
        self,
        key_id: str,
        user_id: str,
        reason: Optional[str] = None,
        grace_period_minutes: int = 0
    ):
        """
        Revoke an API key
        
        Args:
            key_id: ID of key to revoke
            user_id: User performing revocation
            reason: Reason for revocation
            grace_period_minutes: Minutes before revocation takes effect
        """
        # Get key
        api_key = await self._get_api_key(key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Schedule revocation
        if grace_period_minutes > 0:
            revoke_at = datetime.utcnow() + timedelta(minutes=grace_period_minutes)
            api_key["revoke_scheduled_at"] = revoke_at.isoformat()
        else:
            api_key["is_active"] = False
            api_key["revoked_at"] = datetime.utcnow().isoformat()
        
        api_key["revoked_by"] = user_id
        api_key["revoke_reason"] = reason
        
        await self._store_api_key(api_key)
        
        # Log revocation
        if self.config.audit_enabled:
            await self._audit_log(
                "api_key_revoked",
                {
                    "key_id": key_id,
                    "user_id": user_id,
                    "reason": reason,
                    "grace_period_minutes": grace_period_minutes
                }
            )
    
    async def list_api_keys(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        include_revoked: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List API keys for a tenant or user
        
        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID filter
            include_revoked: Whether to include revoked keys
        
        Returns:
            List of API key summaries (without sensitive data)
        """
        keys = []
        
        # Get key IDs
        if user_id:
            key_ids = await self._get_user_key_ids(user_id)
        else:
            key_ids = await self._get_tenant_key_ids(tenant_id)
        
        for key_id in key_ids:
            key_data = await self._get_api_key(key_id)
            if key_data:
                # Filter revoked if needed
                if not include_revoked and not key_data.get("is_active"):
                    continue
                
                # Remove sensitive data
                safe_key = {
                    "key_id": key_data.get("key_id"),
                    "name": key_data.get("name"),
                    "description": key_data.get("description"),
                    "prefix": key_data.get("key_prefix"),
                    "scopes": key_data.get("scopes"),
                    "created_at": key_data.get("created_at"),
                    "expires_at": key_data.get("expires_at"),
                    "last_used_at": key_data.get("last_used_at"),
                    "is_active": key_data.get("is_active"),
                    "is_service_key": key_data.get("is_service_key"),
                    "needs_rotation": self._needs_rotation(key_data)
                }
                keys.append(safe_key)
        
        return keys
    
    async def get_api_key_usage(
        self,
        key_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an API key
        
        Args:
            key_id: API key ID
            start_date: Start of period
            end_date: End of period
        
        Returns:
            Usage statistics
        """
        # Default to last 30 days
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get usage data from Redis
        usage_key = f"api_key_usage:{key_id}:{start_date.date()}:{end_date.date()}"
        usage_data = await self.redis_client.get(usage_key)
        
        if usage_data:
            return json.loads(usage_data)
        
        # Calculate and cache usage stats
        # In production, this would query a time-series database
        stats = {
            "key_id": key_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_exceeded": 0,
            "average_response_time_ms": 0,
            "endpoints_accessed": [],
            "ip_addresses": [],
            "last_used_at": None
        }
        
        # Cache for 1 hour
        await self.redis_client.setex(
            usage_key,
            3600,
            json.dumps(stats)
        )
        
        return stats
    
    # Helper Methods
    
    def _generate_api_key(self) -> str:
        """Generate a new API key"""
        # Generate random bytes
        random_bytes = secrets.token_bytes(self.config.key_length)
        # Encode as URL-safe base64
        key = secrets.token_urlsafe(self.config.key_length)
        # Add prefix
        return f"{self.config.key_prefix}{key}"
    
    def _hash_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        if self.config.hash_algorithm == "sha256":
            return hashlib.sha256(api_key.encode()).hexdigest()
        elif self.config.hash_algorithm == "sha512":
            return hashlib.sha512(api_key.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.config.hash_algorithm}")
    
    def _needs_rotation(self, key_data: Dict[str, Any]) -> bool:
        """Check if key needs rotation"""
        expires_at = key_data.get("expires_at")
        if not expires_at:
            return False
        
        expires_at = datetime.fromisoformat(expires_at)
        warning_date = expires_at - timedelta(days=self.config.rotation_warning_days)
        
        return datetime.utcnow() > warning_date
    
    async def _check_key_limits(self, tenant_id: str, user_id: str):
        """Check if key creation limits are exceeded"""
        # Check user limit
        user_keys = await self._get_user_key_ids(user_id)
        if len(user_keys) >= self.config.max_keys_per_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User has reached maximum of {self.config.max_keys_per_user} API keys"
            )
        
        # Check tenant limit
        tenant_keys = await self._get_tenant_key_ids(tenant_id)
        if len(tenant_keys) >= self.config.max_keys_per_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant has reached maximum of {self.config.max_keys_per_tenant} API keys"
            )
    
    async def _check_rate_limit(
        self,
        key_id: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """Check if rate limit is exceeded"""
        key = f"rate_limit:{key_id}"
        
        # Increment counter
        count = await self.redis_client.incr(key)
        
        # Set expiration on first request
        if count == 1:
            await self.redis_client.expire(key, window_seconds)
        
        return count <= limit
    
    async def _update_last_used(self, key_id: str, request: Optional[Request] = None):
        """Update last used timestamp and track usage"""
        api_key = await self._get_api_key(key_id)
        if api_key:
            api_key["last_used_at"] = datetime.utcnow().isoformat()
            
            # Track IP if enabled
            if self.config.track_ip_addresses and request and request.client:
                last_ips = api_key.get("last_used_ips", [])
                client_ip = request.client.host
                if client_ip not in last_ips:
                    last_ips.append(client_ip)
                    # Keep only last 10 IPs
                    api_key["last_used_ips"] = last_ips[-10:]
            
            await self._store_api_key(api_key)
    
    # Storage Methods
    
    async def _store_api_key(self, api_key: Union[APIKey, Dict[str, Any]]):
        """Store API key in Redis"""
        if isinstance(api_key, APIKey):
            key_dict = api_key.dict()
        else:
            key_dict = api_key
        
        # Convert datetime objects
        for field in ["created_at", "expires_at", "last_used_at", "last_rotated_at", "revoked_at"]:
            if field in key_dict and isinstance(key_dict[field], datetime):
                key_dict[field] = key_dict[field].isoformat()
        
        key_id = key_dict.get("key_id")
        key_hash = key_dict.get("key_hash")
        
        # Store by ID
        await self.redis_client.hset(
            "api_keys",
            key_id,
            json.dumps(key_dict)
        )
        
        # Store hash -> ID mapping
        await self.redis_client.hset(
            "api_key_hashes",
            key_hash,
            key_id
        )
    
    async def _get_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key by ID"""
        data = await self.redis_client.hget("api_keys", key_id)
        if data:
            return json.loads(data)
        return None
    
    async def _get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash"""
        key_id = await self.redis_client.hget("api_key_hashes", key_hash)
        if key_id:
            return await self._get_api_key(key_id)
        return None
    
    async def _track_api_key(self, tenant_id: str, user_id: str, key_id: str):
        """Track API key for tenant and user"""
        # Add to tenant's keys
        await self.redis_client.sadd(f"tenant_keys:{tenant_id}", key_id)
        
        # Add to user's keys
        if user_id:
            await self.redis_client.sadd(f"user_keys:{user_id}", key_id)
    
    async def _get_tenant_key_ids(self, tenant_id: str) -> Set[str]:
        """Get all key IDs for a tenant"""
        return await self.redis_client.smembers(f"tenant_keys:{tenant_id}")
    
    async def _get_user_key_ids(self, user_id: str) -> Set[str]:
        """Get all key IDs for a user"""
        return await self.redis_client.smembers(f"user_keys:{user_id}")
    
    async def _audit_log(self, event_type: str, data: Dict[str, Any]):
        """Log audit event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # Store in Redis list (last 1000 events)
        await self.redis_client.lpush("api_key_audit_log", json.dumps(event))
        await self.redis_client.ltrim("api_key_audit_log", 0, 999)


# Export main classes
__all__ = [
    'APIKeyManager',
    'APIKeyConfig',
    'APIKey',
    'APIKeyScope',
    'APIKeyUsage'
]
