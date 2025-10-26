"""
Production-Grade Authentication and Authorization System
Implements real user authentication with database lookup and RBAC
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from uuid import UUID
import hashlib

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload
import redis.asyncio as redis

from .database import get_db
from .models import Organization, User, Role, Permission, UserRole, RolePermission


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this-in-production":
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable must be set to a secure value"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Redis for distributed rate limiting
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    organization_id: str
    email: str
    roles: List[str] = []
    permissions: List[str] = []
    session_id: Optional[str] = None
    
    
class AuthUser(BaseModel):
    """Authenticated user model"""
    id: UUID
    email: EmailStr
    organization_id: UUID
    first_name: str
    last_name: str
    is_active: bool = True
    is_verified: bool = False
    roles: List[str] = []
    permissions: Set[str] = set()
    mfa_enabled: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


class RBACPermission(BaseModel):
    """RBAC permission model"""
    resource: str
    action: str
    conditions: Optional[Dict[str, Any]] = None
    
    def to_string(self) -> str:
        """Convert to permission string format"""
        return f"{self.resource}:{self.action}"


class ProductionAuthService:
    """Production-grade authentication service with real database integration"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()
    
    async def _init_redis(self):
        """Initialize Redis connection for distributed operations"""
        try:
            self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Rate limiting will be limited.")
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        request: Optional[Request] = None
    ) -> Optional[AuthUser]:
        """
        Authenticate user with real database lookup
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            request: Optional request for logging
            
        Returns:
            AuthUser if authentication successful, None otherwise
        """
        # Check rate limiting
        if await self._is_rate_limited(email, request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Query user from database with organization and roles
        query = (
            select(User)
            .options(
                selectinload(User.organization),
                selectinload(User.user_roles).selectinload(UserRole.role)
                .selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
            .where(User.email == email)
        )
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            await self._record_failed_login(email, request)
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until.isoformat()}"
            )
        
        # Verify password
        if not pwd_context.verify(password, user.password_hash):
            await self._record_failed_login_for_user(db, user, request)
            return None
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Build AuthUser with roles and permissions
        roles = []
        permissions = set()
        
        for user_role in user.user_roles:
            roles.append(user_role.role.name)
            for role_perm in user_role.role.role_permissions:
                permissions.add(f"{role_perm.permission.resource}:{role_perm.permission.action}")
        
        return AuthUser(
            id=user.id,
            email=user.email,
            organization_id=user.organization_id,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=roles,
            permissions=permissions,
            mfa_enabled=user.mfa_enabled,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until
        )
    
    async def _record_failed_login(self, email: str, request: Optional[Request] = None):
        """Record failed login attempt for unknown user"""
        if self.redis_client:
            key = f"failed_login:{email}"
            await self.redis_client.incr(key)
            await self.redis_client.expire(key, 3600)  # 1 hour expiry
    
    async def _record_failed_login_for_user(
        self,
        db: AsyncSession,
        user: User,
        request: Optional[Request] = None
    ):
        """Record failed login attempt for known user"""
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        await db.commit()
        
        # Also record in Redis for distributed rate limiting
        if self.redis_client:
            key = f"failed_login:{user.email}"
            await self.redis_client.incr(key)
            await self.redis_client.expire(key, 3600)
    
    async def _is_rate_limited(self, email: str, request: Optional[Request] = None) -> bool:
        """Check if user is rate limited"""
        if not self.redis_client:
            return False
        
        # Check by email
        email_key = f"failed_login:{email}"
        email_attempts = await self.redis_client.get(email_key)
        if email_attempts and int(email_attempts) > 10:
            return True
        
        # Check by IP if request provided
        if request and request.client:
            ip_key = f"failed_login_ip:{request.client.host}"
            ip_attempts = await self.redis_client.get(ip_key)
            if ip_attempts and int(ip_attempts) > 20:
                return True
        
        return False
    
    def create_access_token(self, user: AuthUser, session_id: Optional[str] = None) -> str:
        """Create JWT access token with user data"""
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(user.organization_id),
            "roles": user.roles,
            "permissions": list(user.permissions),
            "session_id": session_id or secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, user: AuthUser, session_id: Optional[str] = None) -> str:
        """Create JWT refresh token"""
        payload = {
            "sub": str(user.id),
            "session_id": session_id or secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> AuthUser:
        """
        Get current authenticated user from token
        Real implementation with database lookup
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "access":
                raise credentials_exception
            
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            
            # Check token blacklist (for logout)
            if self.redis_client:
                session_id = payload.get("session_id")
                if session_id:
                    is_blacklisted = await self.redis_client.get(f"blacklist:{session_id}")
                    if is_blacklisted:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has been revoked"
                        )
            
        except JWTError:
            raise credentials_exception
        
        # Query real user from database
        query = (
            select(User)
            .options(
                selectinload(User.organization),
                selectinload(User.user_roles).selectinload(UserRole.role)
                .selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
            .where(User.id == UUID(user_id))
        )
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
        
        # Check if user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Build AuthUser
        roles = []
        permissions = set()
        
        for user_role in user.user_roles:
            roles.append(user_role.role.name)
            for role_perm in user_role.role.role_permissions:
                permissions.add(f"{role_perm.permission.resource}:{role_perm.permission.action}")
        
        return AuthUser(
            id=user.id,
            email=user.email,
            organization_id=user.organization_id,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=roles,
            permissions=permissions,
            mfa_enabled=user.mfa_enabled,
            last_login=user.last_login
        )
    
    async def logout(self, token: str, db: AsyncSession):
        """Logout user by blacklisting token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            session_id = payload.get("session_id")
            
            if session_id and self.redis_client:
                # Calculate remaining TTL
                exp = payload.get("exp")
                if exp:
                    ttl = exp - datetime.utcnow().timestamp()
                    if ttl > 0:
                        # Blacklist the session
                        await self.redis_client.setex(
                            f"blacklist:{session_id}",
                            int(ttl),
                            "1"
                        )
        except JWTError:
            pass  # Invalid token, ignore


class RBACService:
    """Role-Based Access Control service"""
    
    def __init__(self):
        self.auth_service = ProductionAuthService()
    
    def has_permission(
        self,
        user: AuthUser,
        resource: str,
        action: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user: Authenticated user
            resource: Resource name (e.g., 'billing', 'invoice', 'user')
            action: Action name (e.g., 'read', 'write', 'delete')
            conditions: Optional conditions for the permission
            
        Returns:
            True if user has permission
        """
        # Check for admin role (has all permissions)
        if 'billing_admin' in user.roles or 'super_admin' in user.roles:
            return True
        
        # Check specific permission
        permission_string = f"{resource}:{action}"
        if permission_string in user.permissions:
            # TODO: Evaluate conditions if provided
            return True
        
        # Check wildcard permissions
        if f"{resource}:*" in user.permissions:
            return True
        
        if f"*:{action}" in user.permissions:
            return True
        
        if "*:*" in user.permissions:
            return True
        
        return False
    
    def require_permission(self, resource: str, action: str):
        """
        FastAPI dependency to require specific permission
        
        Usage:
            @app.get("/invoices", dependencies=[Depends(rbac.require_permission("invoice", "read"))])
        """
        async def permission_checker(
            current_user: AuthUser = Depends(self.auth_service.get_current_user)
        ):
            if not self.has_permission(current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {resource}:{action}"
                )
            return current_user
        
        return permission_checker
    
    def require_role(self, *roles: str):
        """
        FastAPI dependency to require specific role(s)
        
        Usage:
            @app.get("/admin", dependencies=[Depends(rbac.require_role("billing_admin"))])
        """
        async def role_checker(
            current_user: AuthUser = Depends(self.auth_service.get_current_user)
        ):
            if not any(role in current_user.roles for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role(s): {', '.join(roles)}"
                )
            return current_user
        
        return role_checker


# Database Role Definitions (matching SECURITY_FRAMEWORK.md)
DATABASE_ROLES = {
    "billing_admin": {
        "description": "Full administrative access to billing system",
        "permissions": [
            "billing:*",
            "invoice:*",
            "payment:*",
            "subscription:*",
            "user:*",
            "audit:read",
            "settings:*"
        ]
    },
    "billing_operator": {
        "description": "Operational access for billing tasks",
        "permissions": [
            "billing:read",
            "billing:write",
            "invoice:read",
            "invoice:write",
            "payment:read",
            "payment:process",
            "subscription:read",
            "subscription:write",
            "user:read",
            "audit:read"
        ]
    },
    "billing_readonly": {
        "description": "Read-only access to billing data",
        "permissions": [
            "billing:read",
            "invoice:read",
            "payment:read",
            "subscription:read",
            "user:read"
        ]
    },
    "billing_api": {
        "description": "API access for external integrations",
        "permissions": [
            "billing:read",
            "invoice:read",
            "invoice:create",
            "payment:read",
            "subscription:read"
        ]
    }
}


async def initialize_database_roles(db: AsyncSession):
    """Initialize database roles and permissions"""
    for role_name, role_config in DATABASE_ROLES.items():
        # Check if role exists
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        
        if not role:
            # Create role
            role = Role(
                name=role_name,
                description=role_config["description"],
                is_system=True
            )
            db.add(role)
            await db.flush()
        
        # Process permissions
        for perm_string in role_config["permissions"]:
            resource, action = perm_string.split(":")
            
            # Check if permission exists
            result = await db.execute(
                select(Permission).where(
                    and_(
                        Permission.resource == resource,
                        Permission.action == action
                    )
                )
            )
            permission = result.scalar_one_or_none()
            
            if not permission:
                # Create permission
                permission = Permission(
                    resource=resource,
                    action=action,
                    description=f"Permission to {action} {resource}"
                )
                db.add(permission)
                await db.flush()
            
            # Check if role has permission
            result = await db.execute(
                select(RolePermission).where(
                    and_(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id
                    )
                )
            )
            role_perm = result.scalar_one_or_none()
            
            if not role_perm:
                # Grant permission to role
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id
                )
                db.add(role_perm)
    
    await db.commit()


# Initialize services
auth_service = ProductionAuthService()
rbac_service = RBACService()


# Export for use in FastAPI
get_current_user = auth_service.get_current_user
require_permission = rbac_service.require_permission
require_role = rbac_service.require_role
