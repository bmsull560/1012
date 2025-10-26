"""
JWT-based Multi-Tenant Context Enforcement
Ensures all requests are properly authenticated and tenant-isolated
"""

import os
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class TenantContext(BaseModel):
    """Tenant context extracted from JWT claims"""
    tenant_id: str
    org_id: str
    user_id: str
    email: str
    roles: list[str] = []
    permissions: list[str] = []
    
    class Config:
        frozen = True  # Make immutable


class JWTConfig:
    """JWT configuration"""
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    ALGORITHM = os.getenv('JWT_ALGORITHM', 'RS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    ISSUER = os.getenv('JWT_ISSUER', 'valueverse-platform')
    AUDIENCE = os.getenv('JWT_AUDIENCE', 'valueverse-api')
    
    @classmethod
    def validate(cls):
        """Validate JWT configuration on startup"""
        if not cls.SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        
        if cls.ALGORITHM not in ['HS256', 'RS256', 'ES256']:
            raise ValueError(f"Unsupported JWT algorithm: {cls.ALGORITHM}")


class TokenGenerator:
    """Generate JWT tokens with tenant context"""
    
    @staticmethod
    def create_access_token(
        tenant_id: str,
        org_id: str,
        user_id: str,
        email: str,
        roles: list[str] = None,
        permissions: list[str] = None,
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """Create a new access token with tenant context"""
        
        # Token payload
        payload = {
            # Standard claims
            'iss': JWTConfig.ISSUER,
            'aud': JWTConfig.AUDIENCE,
            'sub': user_id,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
            'jti': f"{user_id}-{datetime.utcnow().timestamp()}",
            
            # Tenant context (required)
            'tenant_id': tenant_id,
            'org_id': org_id,
            'user_id': user_id,
            
            # RBAC
            'roles': roles or [],
            'permissions': permissions or [],
            
            # Token type
            'token_type': 'access'
        }
        
        # Add any additional claims
        if additional_claims:
            payload.update(additional_claims)
        
        # Generate token
        token = jwt.encode(
            payload,
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        return token
    
    @staticmethod
    def create_refresh_token(user_id: str, tenant_id: str) -> str:
        """Create a refresh token"""
        
        payload = {
            'iss': JWTConfig.ISSUER,
            'aud': JWTConfig.AUDIENCE,
            'sub': user_id,
            'tenant_id': tenant_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS),
            'token_type': 'refresh'
        }
        
        token = jwt.encode(
            payload,
            JWTConfig.SECRET_KEY,
            algorithm=JWTConfig.ALGORITHM
        )
        
        return token


class TenantContextExtractor:
    """Extract and validate tenant context from JWT"""
    
    @staticmethod
    def extract_from_token(token: str) -> TenantContext:
        """Extract tenant context from JWT token"""
        
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                JWTConfig.SECRET_KEY,
                algorithms=[JWTConfig.ALGORITHM],
                audience=JWTConfig.AUDIENCE,
                issuer=JWTConfig.ISSUER,
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'verify_aud': True,
                    'verify_iss': True,
                    'require': ['tenant_id', 'org_id', 'user_id', 'email']
                }
            )
            
            # Validate token type
            if payload.get('token_type') != 'access':
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            # Create tenant context
            return TenantContext(
                tenant_id=payload['tenant_id'],
                org_id=payload['org_id'],
                user_id=payload['user_id'],
                email=payload['email'],
                roles=payload.get('roles', []),
                permissions=payload.get('permissions', [])
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        except KeyError as e:
            logger.error(f"Missing required claim: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Token missing required claims"
            )


async def get_tenant_context(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TenantContext:
    """
    FastAPI dependency to extract tenant context from JWT.
    This should be used on ALL authenticated endpoints.
    
    Usage:
        @app.get("/api/resource")
        async def get_resource(tenant: TenantContext = Depends(get_tenant_context)):
            # tenant.tenant_id is guaranteed to be present and validated
            return {"tenant_id": tenant.tenant_id}
    """
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    # Extract tenant context from token
    return TenantContextExtractor.extract_from_token(credentials.credentials)


async def require_tenant_context(
    request: Request,
    tenant: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """
    Enhanced dependency that also validates against request headers.
    Prevents tenant spoofing via headers.
    """
    
    # Check if client is trying to spoof tenant via headers
    header_tenant = request.headers.get('X-Tenant-ID')
    if header_tenant and header_tenant != tenant.tenant_id:
        logger.warning(
            f"Tenant spoofing attempt detected. "
            f"JWT tenant: {tenant.tenant_id}, Header tenant: {header_tenant}"
        )
        raise HTTPException(
            status_code=403,
            detail="Tenant context mismatch"
        )
    
    # Add tenant context to request state for downstream use
    request.state.tenant = tenant
    
    return tenant


def require_roles(*required_roles: str):
    """
    Dependency to require specific roles.
    
    Usage:
        @app.post("/api/admin/action")
        async def admin_action(
            tenant: TenantContext = Depends(require_roles("admin", "super_admin"))
        ):
            return {"message": "Admin action performed"}
    """
    
    async def role_checker(
        tenant: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        
        # Check if user has any of the required roles
        if not any(role in tenant.roles for role in required_roles):
            logger.warning(
                f"Access denied for user {tenant.user_id}. "
                f"Required roles: {required_roles}, User roles: {tenant.roles}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(required_roles)}"
            )
        
        return tenant
    
    return role_checker


def require_permissions(*required_permissions: str):
    """
    Dependency to require specific permissions.
    
    Usage:
        @app.delete("/api/resource/{id}")
        async def delete_resource(
            id: str,
            tenant: TenantContext = Depends(require_permissions("resource:delete"))
        ):
            return {"deleted": id}
    """
    
    async def permission_checker(
        tenant: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        
        # Check if user has all required permissions
        missing_permissions = [
            perm for perm in required_permissions 
            if perm not in tenant.permissions
        ]
        
        if missing_permissions:
            logger.warning(
                f"Access denied for user {tenant.user_id}. "
                f"Missing permissions: {missing_permissions}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return tenant
    
    return permission_checker


class TenantIsolationMiddleware:
    """
    Middleware to enforce tenant isolation on all requests.
    This should be added to the FastAPI app to ensure no request
    can bypass tenant validation.
    """
    
    def __init__(self, app):
        self.app = app
        
        # Paths that don't require authentication
        self.public_paths = {
            '/health',
            '/metrics',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/api/auth/login',
            '/api/auth/refresh',
            '/api/auth/register'
        }
    
    async def __call__(self, request: Request, call_next):
        # Skip authentication for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # For all other paths, validate JWT and extract tenant
        try:
            # Get authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authorization header missing or invalid"}
                )
            
            # Extract token
            token = auth_header.split(' ')[1]
            
            # Extract tenant context
            tenant = TenantContextExtractor.extract_from_token(token)
            
            # Add to request state
            request.state.tenant = tenant
            
            # Log the request with tenant context
            logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    "tenant_id": tenant.tenant_id,
                    "user_id": tenant.user_id,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            
            # Process request
            response = await call_next(request)
            
            # Add tenant ID to response headers for debugging
            response.headers["X-Tenant-ID"] = tenant.tenant_id
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unexpected error in tenant isolation: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )


# Validate configuration on module import
JWTConfig.validate()


# Export key components
__all__ = [
    'TenantContext',
    'TenantContextExtractor',
    'TokenGenerator',
    'get_tenant_context',
    'require_tenant_context',
    'require_roles',
    'require_permissions',
    'TenantIsolationMiddleware',
    'JWTConfig'
]
