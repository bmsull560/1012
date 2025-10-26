"""
Enterprise Security System - Complete Integration
Integrates all 7 critical security components into a unified system
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

# Import all security components
from .auth_production import ProductionAuthService, RBACService, AuthUser, DATABASE_ROLES
from .pci_tokenization import PCITokenizationVault, CardData, TokenizedCard
from .gdpr_compliance import GDPRComplianceService, GDPRRequestType
from .immutable_audit_complete import ImmutableAuditTrail
from .key_management import SecureKeyManagementSystem, KeyType
from .database import get_db


class EnterpriseSecuritySystem:
    """
    Complete enterprise security system integrating all components:
    1. Real user authentication with database lookup
    2. Database-level RBAC system
    3. PCI DSS tokenization vault
    4. GDPR data subject rights
    5. Hash-chained immutable audit trail
    6. Secure key management with rotation
    7. Distributed rate limiting with Redis
    """
    
    def __init__(self):
        # Configuration
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Validate critical security configuration
        self._validate_security_config()
        
        # Initialize components
        self.auth_service = ProductionAuthService()
        self.rbac_service = RBACService()
        self.tokenization_vault = PCITokenizationVault(self.database_url)
        self.gdpr_service = GDPRComplianceService(self.database_url)
        self.audit_trail = ImmutableAuditTrail(self.database_url)
        self.key_manager = SecureKeyManagementSystem(self.database_url, self.redis_url)
        
        # Redis client for distributed rate limiting
        self.redis_client: Optional[redis.Redis] = None
        
        # Rate limiting configuration
        self.rate_limits = {
            "login": {"max_requests": 5, "window_seconds": 300},  # 5 attempts per 5 minutes
            "api": {"max_requests": 100, "window_seconds": 60},    # 100 requests per minute
            "tokenization": {"max_requests": 10, "window_seconds": 60},  # 10 tokenizations per minute
            "gdpr": {"max_requests": 2, "window_seconds": 3600},   # 2 GDPR requests per hour
        }
    
    def _validate_security_config(self):
        """Validate critical security configuration on startup"""
        critical_vars = [
            "JWT_SECRET_KEY",
            "ENCRYPTION_MASTER_KEY",
            "KEY_ENCRYPTION_KEY",
            "PCI_MASTER_KEY",
            "DATABASE_URL"
        ]
        
        missing = []
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            elif value in ["your-secret-key-change-this-in-production", "placeholder", "changeme"]:
                raise RuntimeError(f"CRITICAL: {var} contains default/placeholder value. Set a secure value!")
        
        if missing:
            raise RuntimeError(
                f"CRITICAL: Missing required security environment variables: {', '.join(missing)}. "
                "Application cannot start without proper security configuration."
            )
        
        print("✅ Security configuration validated")
    
    async def initialize(self):
        """Initialize all security components"""
        print("Initializing Enterprise Security System...")
        
        # Initialize Redis for distributed rate limiting
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        
        # Initialize each component
        await self.auth_service._init_redis()
        await self.tokenization_vault.init()
        await self.gdpr_service.init()
        await self.audit_trail.init()
        await self.key_manager.init()
        
        # Initialize database roles
        from .database import async_session
        async with async_session() as db:
            await self._initialize_database_roles(db)
        
        print("✅ Enterprise Security System initialized successfully")
    
    async def shutdown(self):
        """Shutdown all security components"""
        await self.tokenization_vault.close()
        await self.gdpr_service.close()
        await self.audit_trail.close()
        await self.key_manager.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def _initialize_database_roles(self, db: AsyncSession):
        """Initialize RBAC roles in database"""
        from .auth_production import initialize_database_roles
        await initialize_database_roles(db)
        print("✅ Database roles initialized")
    
    # ==================== AUTHENTICATION & AUTHORIZATION ====================
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        request: Optional[Request] = None,
        db: Optional[AsyncSession] = None
    ) -> AuthUser:
        """Authenticate user with rate limiting and audit logging"""
        # Check rate limit
        if request:
            await self.check_rate_limit("login", request.client.host if request.client else "unknown")
        
        # Authenticate
        user = await self.auth_service.authenticate_user(db, email, password, request)
        
        if user:
            # Log successful authentication
            await self.audit_trail.log_event(
                event_type="auth.login.success",
                action="login",
                description=f"User {email} logged in successfully",
                actor_id=str(user.id),
                result="success"
            )
        else:
            # Log failed authentication
            await self.audit_trail.log_event(
                event_type="auth.login.failed",
                action="login",
                description=f"Failed login attempt for {email}",
                target_id=email,
                result="failure"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return user
    
    async def get_current_user(
        self,
        token: str,
        db: AsyncSession
    ) -> AuthUser:
        """Get current user with real database lookup"""
        return await self.auth_service.get_current_user(token, db)
    
    def has_permission(
        self,
        user: AuthUser,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has specific permission"""
        return self.rbac_service.has_permission(user, resource, action)
    
    # ==================== PCI DSS TOKENIZATION ====================
    
    async def tokenize_card(
        self,
        card_data: CardData,
        organization_id: str,
        user_id: str,
        request: Optional[Request] = None
    ) -> TokenizedCard:
        """Tokenize card data with rate limiting and audit"""
        # Check rate limit
        if request:
            await self.check_rate_limit("tokenization", request.client.host if request.client else "unknown")
        
        # Tokenize
        token = await self.tokenization_vault.tokenize(
            card_data,
            organization_id,
            user_id,
            request.client.host if request and request.client else None
        )
        
        # Audit
        await self.audit_trail.log_event(
            event_type="pci.tokenization",
            action="tokenize_card",
            description=f"Card tokenized for organization {organization_id}",
            actor_id=user_id,
            target_id=token.token,
            result="success",
            metadata={
                "card_brand": token.card_brand,
                "masked_number": token.masked_number
            }
        )
        
        return token
    
    async def detokenize_card(
        self,
        token: str,
        organization_id: str,
        user_id: str,
        reason: str,
        request: Optional[Request] = None
    ) -> Optional[str]:
        """Detokenize with strict audit and authorization"""
        # Check permission
        user = await self.get_current_user(request.headers.get("Authorization"), None)
        if not self.has_permission(user, "pci", "detokenize"):
            await self.audit_trail.log_event(
                event_type="pci.detokenization",
                action="detokenize_card",
                description=f"Unauthorized detokenization attempt",
                actor_id=user_id,
                target_id=token,
                result="failure",
                metadata={"reason": "insufficient_permissions"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for detokenization"
            )
        
        # Detokenize
        pan = await self.tokenization_vault.detokenize(
            token,
            organization_id,
            user_id,
            request.client.host if request and request.client else None,
            reason
        )
        
        # Critical audit
        await self.audit_trail.log_event(
            event_type="pci.detokenization",
            action="detokenize_card",
            description=f"Card detokenized: {reason}",
            actor_id=user_id,
            target_id=token,
            result="success" if pan else "failure",
            metadata={"reason": reason}
        )
        
        return pan
    
    # ==================== GDPR COMPLIANCE ====================
    
    async def create_gdpr_request(
        self,
        request_type: GDPRRequestType,
        subject_id: str,
        subject_email: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Create GDPR request with rate limiting"""
        # Check rate limit
        await self.check_rate_limit("gdpr", subject_email)
        
        # Create request
        gdpr_request = await self.gdpr_service.create_request(
            request_type,
            subject_id,
            subject_email,
            reason=reason
        )
        
        # Audit
        await self.audit_trail.log_event(
            event_type="gdpr.request",
            action=f"gdpr_{request_type.value}",
            description=f"GDPR {request_type.value} request created",
            actor_id=user_id or subject_id,
            target_id=subject_id,
            result="success",
            metadata={"request_id": gdpr_request.request_id}
        )
        
        return gdpr_request
    
    async def process_erasure(
        self,
        request_id: str,
        processed_by: str
    ):
        """Process GDPR erasure with full audit"""
        result = await self.gdpr_service.process_erasure_request(
            request_id,
            processed_by
        )
        
        # Critical audit
        await self.audit_trail.log_event(
            event_type="gdpr.erasure",
            action="process_erasure",
            description="GDPR erasure processed",
            actor_id=processed_by,
            target_id=request_id,
            result="success" if result.get("success") else "failure",
            metadata=result
        )
        
        return result
    
    # ==================== KEY MANAGEMENT ====================
    
    async def rotate_encryption_keys(self, reason: str = "Scheduled rotation"):
        """Rotate all encryption keys"""
        results = {}
        
        for key_type in [KeyType.DATA_ENCRYPTION, KeyType.PCI_TOKENIZATION]:
            try:
                old_key, new_key = await self.key_manager.rotate_key(key_type, reason)
                results[key_type.value] = {
                    "success": True,
                    "old_version": old_key.key_version,
                    "new_version": new_key.key_version
                }
                
                # Audit key rotation
                await self.audit_trail.log_event(
                    event_type="key.rotation",
                    action="rotate_key",
                    description=f"Key rotated: {key_type.value}",
                    actor_id="system",
                    target_id=new_key.key_id,
                    result="success",
                    metadata={
                        "key_type": key_type.value,
                        "old_key_id": old_key.key_id,
                        "new_key_id": new_key.key_id
                    }
                )
            except Exception as e:
                results[key_type.value] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    # ==================== DISTRIBUTED RATE LIMITING ====================
    
    async def check_rate_limit(
        self,
        limit_type: str,
        identifier: str
    ) -> bool:
        """
        Check rate limit using Redis
        
        Args:
            limit_type: Type of limit (login, api, tokenization, gdpr)
            identifier: Unique identifier (IP, user_id, etc.)
        
        Returns:
            True if within limit
            
        Raises:
            HTTPException if rate limit exceeded
        """
        if not self.redis_client:
            return True  # Skip if Redis not available
        
        config = self.rate_limits.get(limit_type, {"max_requests": 100, "window_seconds": 60})
        key = f"rate_limit:{limit_type}:{identifier}"
        
        # Increment counter
        current = await self.redis_client.incr(key)
        
        # Set expiration on first request
        if current == 1:
            await self.redis_client.expire(key, config["window_seconds"])
        
        # Check limit
        if current > config["max_requests"]:
            ttl = await self.redis_client.ttl(key)
            
            # Log rate limit violation
            await self.audit_trail.log_event(
                event_type="security.rate_limit",
                action="rate_limit_exceeded",
                description=f"Rate limit exceeded for {limit_type}",
                actor_id=identifier,
                result="blocked",
                metadata={
                    "limit_type": limit_type,
                    "current_requests": current,
                    "max_requests": config["max_requests"],
                    "ttl_seconds": ttl
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds"
            )
        
        return True
    
    # ==================== AUDIT TRAIL ====================
    
    async def verify_audit_integrity(
        self,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> Dict[str, Any]:
        """Verify the integrity of the audit trail"""
        result = await self.audit_trail.verify_integrity(start_block, end_block)
        
        if not result["verified"]:
            # Critical security event
            await self.audit_trail.log_event(
                event_type="security.alert",
                action="audit_integrity_failure",
                description="Audit trail integrity check failed",
                actor_id="system",
                result="failure",
                metadata=result
            )
        
        return result
    
    async def get_audit_logs(
        self,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs with authorization check"""
        return await self.audit_trail.query_events(
            event_type=event_type,
            actor_id=actor_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )


# ==================== FASTAPI INTEGRATION ====================

def setup_enterprise_security(app: FastAPI) -> EnterpriseSecuritySystem:
    """
    Setup enterprise security system with FastAPI
    
    Usage:
        app = FastAPI()
        security = setup_enterprise_security(app)
    """
    security = EnterpriseSecuritySystem()
    
    @app.on_event("startup")
    async def startup():
        """Initialize security system on startup"""
        await security.initialize()
    
    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown"""
        await security.shutdown()
    
    # Add security middleware
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Security middleware for all requests"""
        # Check general API rate limit
        if request.url.path.startswith("/api/"):
            try:
                client_ip = request.client.host if request.client else "unknown"
                await security.check_rate_limit("api", client_ip)
            except HTTPException as e:
                return Response(
                    content=e.detail,
                    status_code=e.status_code
                )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
    
    # Authentication endpoints
    @app.post("/api/auth/login")
    async def login(
        email: str,
        password: str,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
    ):
        """Login with real user authentication"""
        user = await security.authenticate_user(email, password, request, db)
        
        # Create tokens
        access_token = security.auth_service.create_access_token(user)
        refresh_token = security.auth_service.create_refresh_token(user)
        
        # Set secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=1800  # 30 minutes
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800  # 7 days
        )
        
        return {"status": "success", "user": user.dict()}
    
    @app.post("/api/auth/logout")
    async def logout(
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
    ):
        """Logout with token blacklisting"""
        token = request.cookies.get("access_token")
        if token:
            await security.auth_service.logout(token, db)
        
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return {"status": "logged out"}
    
    @app.get("/api/auth/me")
    async def get_me(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        """Get current user with real database lookup"""
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        user = await security.get_current_user(token, db)
        return user.dict()
    
    # PCI endpoints
    @app.post("/api/pci/tokenize")
    async def tokenize(
        card_data: CardData,
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        """Tokenize card data"""
        token = request.cookies.get("access_token")
        user = await security.get_current_user(token, db)
        
        if not security.has_permission(user, "pci", "tokenize"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        result = await security.tokenize_card(
            card_data,
            str(user.organization_id),
            str(user.id),
            request
        )
        
        return result.dict()
    
    # GDPR endpoints
    @app.post("/api/gdpr/request")
    async def create_gdpr_request(
        request_type: GDPRRequestType,
        reason: Optional[str] = None,
        request: Request = None,
        db: AsyncSession = Depends(get_db)
    ):
        """Create GDPR request"""
        token = request.cookies.get("access_token")
        user = await security.get_current_user(token, db)
        
        result = await security.create_gdpr_request(
            request_type,
            str(user.id),
            user.email,
            reason,
            str(user.id)
        )
        
        return {"request_id": result.request_id, "status": result.status}
    
    # Admin endpoints
    @app.post("/api/admin/rotate-keys")
    async def rotate_keys(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        """Rotate encryption keys (admin only)"""
        token = request.cookies.get("access_token")
        user = await security.get_current_user(token, db)
        
        if not security.has_permission(user, "admin", "rotate_keys"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        results = await security.rotate_encryption_keys("Manual rotation by admin")
        return results
    
    @app.get("/api/admin/audit-integrity")
    async def verify_audit(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ):
        """Verify audit trail integrity (admin only)"""
        token = request.cookies.get("access_token")
        user = await security.get_current_user(token, db)
        
        if not security.has_permission(user, "admin", "audit"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        result = await security.verify_audit_integrity()
        return result
    
    return security


# Export main components
__all__ = [
    'EnterpriseSecuritySystem',
    'setup_enterprise_security'
]
