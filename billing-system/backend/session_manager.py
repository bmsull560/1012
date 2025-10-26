"""
Enhanced Session Management with Token Revocation
Implements secure session handling with Redis-based token blacklisting
"""

import os
import json
import secrets
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import redis.asyncio as redis
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel, Field
from jose import JWTError, jwt
import hashlib


class SessionConfig(BaseModel):
    """Configuration for session management"""
    access_token_expire_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    max_sessions_per_user: int = Field(default=5, ge=1, le=20)
    session_timeout_minutes: int = Field(default=30, ge=5, le=120)
    enable_device_fingerprinting: bool = True
    enable_ip_tracking: bool = True
    enable_user_agent_tracking: bool = True
    require_secure_cookie: bool = True
    same_site_policy: str = Field(default="strict", pattern="^(strict|lax|none)$")


class DeviceFingerprint(BaseModel):
    """Device fingerprint for session tracking"""
    user_agent: str
    accept_language: Optional[str] = None
    accept_encoding: Optional[str] = None
    ip_address: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    platform: Optional[str] = None
    
    def generate_hash(self) -> str:
        """Generate a unique hash for this device fingerprint"""
        data = f"{self.user_agent}:{self.ip_address}:{self.platform}"
        return hashlib.sha256(data.encode()).hexdigest()


class Session(BaseModel):
    """Session model"""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    device_fingerprint: Optional[DeviceFingerprint] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None


class SessionManager:
    """
    Enhanced session management with Redis-based token revocation
    Implements secure session handling and token blacklisting
    """
    
    def __init__(
        self,
        redis_url: str,
        secret_key: str,
        algorithm: str = "HS256",
        config: Optional[SessionConfig] = None
    ):
        """Initialize session manager"""
        self.redis_url = redis_url
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.config = config or SessionConfig()
        self.redis_client: Optional[redis.Redis] = None
    
    async def init(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def create_session(
        self,
        user_id: str,
        request: Optional[Request] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session for a user
        
        Args:
            user_id: User ID
            request: FastAPI request object for extracting device info
            device_info: Additional device information
        
        Returns:
            Created session object
        """
        # Check if user has reached max sessions
        await self._check_max_sessions(user_id)
        
        # Create device fingerprint if enabled
        device_fingerprint = None
        if self.config.enable_device_fingerprinting and request:
            device_fingerprint = self._create_device_fingerprint(request, device_info)
        
        # Generate tokens
        access_token_data = {
            "user_id": user_id,
            "session_id": str(uuid4()),
            "type": "access"
        }
        refresh_token_data = {
            "user_id": user_id,
            "session_id": access_token_data["session_id"],
            "type": "refresh"
        }
        
        access_token = self._create_token(
            access_token_data,
            timedelta(minutes=self.config.access_token_expire_minutes)
        )
        refresh_token = self._create_token(
            refresh_token_data,
            timedelta(days=self.config.refresh_token_expire_days)
        )
        
        # Create session
        session = Session(
            session_id=access_token_data["session_id"],
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days),
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("User-Agent") if request else None
        )
        
        # Store session in Redis
        await self._store_session(session)
        
        # Track active session
        await self._track_active_session(user_id, session.session_id)
        
        return session
    
    async def validate_token(
        self,
        token: str,
        token_type: str = "access"
    ) -> Dict[str, Any]:
        """
        Validate a token and check if it's revoked
        
        Args:
            token: JWT token to validate
            token_type: Type of token (access or refresh)
        
        Returns:
            Token payload if valid
        
        Raises:
            HTTPException: If token is invalid or revoked
        """
        # Check if token is blacklisted
        if await self._is_token_revoked(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Check session validity
            session_id = payload.get("session_id")
            if session_id:
                session = await self._get_session(session_id)
                if not session or not session.get("is_active"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session is no longer active"
                    )
                
                # Update last activity
                await self._update_session_activity(session_id)
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def refresh_session(
        self,
        refresh_token: str,
        request: Optional[Request] = None
    ) -> Dict[str, str]:
        """
        Refresh a session using refresh token
        
        Args:
            refresh_token: Refresh token
            request: FastAPI request for device validation
        
        Returns:
            New access and refresh tokens
        """
        # Validate refresh token
        payload = await self.validate_token(refresh_token, "refresh")
        
        # Get session
        session_id = payload.get("session_id")
        session = await self._get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found"
            )
        
        # Validate device fingerprint if enabled
        if self.config.enable_device_fingerprinting and request:
            current_fingerprint = self._create_device_fingerprint(request)
            stored_fingerprint = session.get("device_fingerprint")
            if stored_fingerprint and current_fingerprint.generate_hash() != stored_fingerprint:
                # Device mismatch - potential security issue
                await self.revoke_session(
                    session_id,
                    reason="Device fingerprint mismatch"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Device verification failed"
                )
        
        # Revoke old tokens
        await self._revoke_token(session.get("access_token"))
        await self._revoke_token(refresh_token)
        
        # Generate new tokens
        new_access_token = self._create_token(
            {
                "user_id": payload["user_id"],
                "session_id": session_id,
                "type": "access"
            },
            timedelta(minutes=self.config.access_token_expire_minutes)
        )
        new_refresh_token = self._create_token(
            {
                "user_id": payload["user_id"],
                "session_id": session_id,
                "type": "refresh"
            },
            timedelta(days=self.config.refresh_token_expire_days)
        )
        
        # Update session
        session["access_token"] = new_access_token
        session["refresh_token"] = new_refresh_token
        session["last_activity"] = datetime.utcnow().isoformat()
        await self._store_session(session)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    
    async def revoke_session(
        self,
        session_id: str,
        reason: Optional[str] = None
    ):
        """Revoke a specific session"""
        session = await self._get_session(session_id)
        if session:
            # Revoke tokens
            await self._revoke_token(session.get("access_token"))
            await self._revoke_token(session.get("refresh_token"))
            
            # Update session
            session["is_active"] = False
            session["revoked_at"] = datetime.utcnow().isoformat()
            session["revoke_reason"] = reason
            await self._store_session(session)
            
            # Remove from active sessions
            user_id = session.get("user_id")
            if user_id:
                await self._remove_active_session(user_id, session_id)
    
    async def revoke_all_user_sessions(
        self,
        user_id: str,
        reason: Optional[str] = None,
        except_current: Optional[str] = None
    ):
        """
        Revoke all sessions for a user
        
        Args:
            user_id: User ID
            reason: Reason for revocation
            except_current: Session ID to exclude (keep current session)
        """
        # Get all active sessions for user
        session_ids = await self._get_user_sessions(user_id)
        
        for session_id in session_ids:
            if session_id != except_current:
                await self.revoke_session(session_id, reason)
    
    async def logout(
        self,
        access_token: str,
        refresh_token: Optional[str] = None
    ):
        """
        Logout user by revoking tokens
        
        Args:
            access_token: Access token to revoke
            refresh_token: Optional refresh token to revoke
        """
        # Decode token to get session ID
        try:
            payload = jwt.decode(
                access_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Token might be expired
            )
            session_id = payload.get("session_id")
            if session_id:
                await self.revoke_session(session_id, "User logout")
        except JWTError:
            # Still revoke the token even if decode fails
            await self._revoke_token(access_token)
            if refresh_token:
                await self._revoke_token(refresh_token)
    
    async def get_active_sessions(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        session_ids = await self._get_user_sessions(user_id)
        sessions = []
        
        for session_id in session_ids:
            session = await self._get_session(session_id)
            if session and session.get("is_active"):
                # Remove sensitive data
                safe_session = {
                    "session_id": session_id,
                    "created_at": session.get("created_at"),
                    "last_activity": session.get("last_activity"),
                    "ip_address": session.get("ip_address"),
                    "user_agent": session.get("user_agent")
                }
                sessions.append(safe_session)
        
        return sessions
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions and tokens"""
        # This should be run periodically (e.g., daily)
        # Implementation depends on your Redis key structure
        pass
    
    # Private methods
    
    def _create_token(
        self,
        data: Dict[str, Any],
        expires_delta: timedelta
    ) -> str:
        """Create a JWT token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def _create_device_fingerprint(
        self,
        request: Request,
        device_info: Optional[Dict[str, Any]] = None
    ) -> DeviceFingerprint:
        """Create device fingerprint from request"""
        fingerprint = DeviceFingerprint(
            user_agent=request.headers.get("User-Agent", ""),
            accept_language=request.headers.get("Accept-Language"),
            accept_encoding=request.headers.get("Accept-Encoding"),
            ip_address=request.client.host if request.client else None
        )
        
        if device_info:
            fingerprint.screen_resolution = device_info.get("screen_resolution")
            fingerprint.timezone = device_info.get("timezone")
            fingerprint.platform = device_info.get("platform")
        
        return fingerprint
    
    async def _store_session(self, session: Union[Session, Dict[str, Any]]):
        """Store session in Redis"""
        if isinstance(session, Session):
            session_dict = session.dict()
        else:
            session_dict = session
        
        # Convert datetime objects to ISO format
        for key in ["created_at", "last_activity", "expires_at", "revoked_at"]:
            if key in session_dict and isinstance(session_dict[key], datetime):
                session_dict[key] = session_dict[key].isoformat()
        
        # Store in Redis with expiration
        session_id = session_dict.get("session_id")
        expire_seconds = self.config.refresh_token_expire_days * 24 * 3600
        
        await self.redis_client.setex(
            f"session:{session_id}",
            expire_seconds,
            json.dumps(session_dict)
        )
    
    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from Redis"""
        data = await self.redis_client.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    async def _update_session_activity(self, session_id: str):
        """Update session last activity"""
        session = await self._get_session(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()
            await self._store_session(session)
    
    async def _track_active_session(self, user_id: str, session_id: str):
        """Track active session for user"""
        await self.redis_client.sadd(f"user_sessions:{user_id}", session_id)
    
    async def _remove_active_session(self, user_id: str, session_id: str):
        """Remove session from active tracking"""
        await self.redis_client.srem(f"user_sessions:{user_id}", session_id)
    
    async def _get_user_sessions(self, user_id: str) -> Set[str]:
        """Get all session IDs for a user"""
        return await self.redis_client.smembers(f"user_sessions:{user_id}")
    
    async def _check_max_sessions(self, user_id: str):
        """Check if user has reached max sessions"""
        sessions = await self._get_user_sessions(user_id)
        if len(sessions) >= self.config.max_sessions_per_user:
            # Revoke oldest session
            oldest_session = None
            oldest_time = datetime.utcnow()
            
            for session_id in sessions:
                session = await self._get_session(session_id)
                if session:
                    created_at = datetime.fromisoformat(session.get("created_at"))
                    if created_at < oldest_time:
                        oldest_time = created_at
                        oldest_session = session_id
            
            if oldest_session:
                await self.revoke_session(
                    oldest_session,
                    "Maximum sessions exceeded"
                )
    
    async def _revoke_token(self, token: Optional[str]):
        """Add token to revocation list"""
        if not token:
            return
        
        try:
            # Decode to get expiration
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            exp = payload.get("exp")
            
            if exp:
                # Calculate TTL
                expire_time = datetime.fromtimestamp(exp)
                ttl = int((expire_time - datetime.utcnow()).total_seconds())
                
                if ttl > 0:
                    # Add to blacklist with TTL
                    token_hash = hashlib.sha256(token.encode()).hexdigest()
                    await self.redis_client.setex(
                        f"revoked_token:{token_hash}",
                        ttl,
                        "1"
                    )
        except JWTError:
            # If decode fails, add with default TTL
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            await self.redis_client.setex(
                f"revoked_token:{token_hash}",
                self.config.refresh_token_expire_days * 24 * 3600,
                "1"
            )
    
    async def _is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return await self.redis_client.exists(f"revoked_token:{token_hash}") > 0


# Export main classes
__all__ = [
    'SessionManager',
    'SessionConfig',
    'Session',
    'DeviceFingerprint'
]
