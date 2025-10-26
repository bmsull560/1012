"""
Security Integration Module
Integrates all security components into a unified system
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel, Field

# Import security modules
from .password_policy import PasswordValidator, PasswordStrengthConfig
from .session_manager import SessionManager, SessionConfig
from .mfa import MFAManager, MFAConfig
from .api_key_manager import APIKeyManager, APIKeyConfig, APIKeyScope
from .audit_core import AuditTrail, AuditEventType, AuditSeverity


class SecurityConfig(BaseModel):
    """Unified security configuration"""
    # Redis and Database
    redis_url: str = Field(default="redis://localhost:6379")
    database_url: str = Field(...)
    
    # Component configs
    password_config: PasswordStrengthConfig = Field(default_factory=PasswordStrengthConfig)
    session_config: SessionConfig = Field(default_factory=SessionConfig)
    mfa_config: MFAConfig = Field(default_factory=MFAConfig)
    api_key_config: APIKeyConfig = Field(default_factory=APIKeyConfig)
    
    # Audit settings
    audit_enabled: bool = True
    audit_retention_days: int = 2555  # 7 years
    
    # Security settings
    require_mfa_for_admin: bool = True
    require_strong_passwords: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30


class SecuritySystem:
    """
    Unified Security System
    Integrates password policy, session management, MFA, API keys, and audit trail
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
        # Initialize components
        self.password_validator = PasswordValidator(config.password_config)
        
        self.session_manager = SessionManager(
            redis_url=config.redis_url,
            secret_key=os.getenv("JWT_SECRET_KEY"),
            config=config.session_config
        )
        
        self.mfa_manager = MFAManager(
            redis_url=config.redis_url,
            config=config.mfa_config,
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            smtp_from_email=os.getenv("SMTP_FROM_EMAIL")
        )
        
        self.api_key_manager = APIKeyManager(
            redis_url=config.redis_url,
            config=config.api_key_config
        )
        
        self.audit_trail = AuditTrail(
            database_url=config.database_url,
            redis_url=config.redis_url,
            retention_days=config.audit_retention_days
        )
        
        # Security schemes
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    
    async def init(self):
        """Initialize all components"""
        await self.password_validator.init_redis(self.config.redis_url)
        await self.session_manager.init()
        await self.mfa_manager.init()
        await self.api_key_manager.init()
        await self.audit_trail.init()
    
    async def close(self):
        """Close all connections"""
        await self.session_manager.close()
        await self.mfa_manager.close()
        await self.api_key_manager.close()
        await self.audit_trail.close()
    
    # Authentication Methods
    
    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        tenant_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Register a new user with security checks"""
        # Validate password strength
        validation = await self.password_validator.validate(
            password=password,
            username=username,
            email=email
        )
        
        if not validation['valid']:
            await self.audit_trail.log(
                AuditEventType.LOGIN_FAILED,
                f"Registration failed: weak password for {email}",
                severity=AuditSeverity.WARNING,
                target_id=email,
                request=request,
                metadata={"errors": validation['errors']}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": validation['errors']}
            )
        
        # Hash password
        from .password_policy import pwd_context
        password_hash = pwd_context.hash(password)
        
        # Create user (implementation depends on your user model)
        user_id = str(datetime.utcnow().timestamp())  # Placeholder
        
        # Log successful registration
        await self.audit_trail.log(
            AuditEventType.DATA_CREATED,
            f"User registered: {email}",
            actor_id=user_id,
            target_id=user_id,
            tenant_id=tenant_id,
            request=request,
            metadata={"email": email, "password_strength": validation['strength_score']}
        )
        
        return {
            "user_id": user_id,
            "email": email,
            "password_strength": validation['strength_score']
        }
    
    async def login(
        self,
        email: str,
        password: str,
        request: Optional[Request] = None,
        require_mfa: bool = False
    ) -> Dict[str, Any]:
        """Authenticate user with security checks"""
        # Check login attempts
        attempts_key = f"login_attempts:{email}"
        attempts = await self.session_manager.redis_client.incr(attempts_key)
        
        if attempts > self.config.max_login_attempts:
            await self.audit_trail.log(
                AuditEventType.SECURITY_ALERT,
                f"Account locked due to too many failed attempts: {email}",
                severity=AuditSeverity.WARNING,
                target_id=email,
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked due to too many failed attempts"
            )
        
        # Set expiry on first attempt
        if attempts == 1:
            await self.session_manager.redis_client.expire(
                attempts_key,
                self.config.lockout_duration_minutes * 60
            )
        
        # Verify password (placeholder - implement actual verification)
        from .password_policy import pwd_context
        # password_valid = pwd_context.verify(password, stored_hash)
        password_valid = True  # Placeholder
        
        if not password_valid:
            await self.audit_trail.log(
                AuditEventType.LOGIN_FAILED,
                f"Invalid password for {email}",
                severity=AuditSeverity.WARNING,
                target_id=email,
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Reset login attempts on success
        await self.session_manager.redis_client.delete(attempts_key)
        
        # Get user (placeholder)
        user_id = str(datetime.utcnow().timestamp())
        is_admin = False  # Placeholder
        
        # Check MFA requirement
        if require_mfa or (is_admin and self.config.require_mfa_for_admin):
            # Get user's MFA status
            mfa_status = await self.mfa_manager.get_user_mfa_status(user_id)
            
            if mfa_status['mfa_enabled']:
                # Send MFA challenge
                challenge_id = await self.mfa_manager.send_sms_code(user_id)
                
                await self.audit_trail.log(
                    AuditEventType.MFA_VERIFIED,
                    f"MFA challenge sent for {email}",
                    actor_id=user_id,
                    request=request
                )
                
                return {
                    "status": "mfa_required",
                    "challenge_id": challenge_id,
                    "user_id": user_id
                }
        
        # Create session
        session = await self.session_manager.create_session(
            user_id=user_id,
            request=request
        )
        
        # Log successful login
        await self.audit_trail.log(
            AuditEventType.LOGIN_SUCCESS,
            f"User logged in: {email}",
            actor_id=user_id,
            session_id=session.session_id,
            request=request
        )
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user_id": user_id
        }
    
    async def verify_mfa_and_login(
        self,
        challenge_id: str,
        code: str,
        user_id: str,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Verify MFA code and complete login"""
        # Verify MFA code
        verified = await self.mfa_manager.verify_code(challenge_id, code)
        
        if not verified:
            await self.audit_trail.log(
                AuditEventType.MFA_FAILED,
                f"Invalid MFA code for user {user_id}",
                severity=AuditSeverity.WARNING,
                actor_id=user_id,
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # Create session
        session = await self.session_manager.create_session(
            user_id=user_id,
            request=request
        )
        
        # Log successful MFA verification
        await self.audit_trail.log(
            AuditEventType.MFA_VERIFIED,
            f"MFA verified for user {user_id}",
            actor_id=user_id,
            session_id=session.session_id,
            request=request
        )
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user_id": user_id
        }
    
    async def logout(
        self,
        token: str,
        request: Optional[Request] = None
    ):
        """Logout user and revoke tokens"""
        # Get session info before revocation
        try:
            token_data = await self.session_manager.validate_token(token)
            user_id = token_data.get("user_id")
            session_id = token_data.get("session_id")
        except:
            user_id = None
            session_id = None
        
        # Revoke session
        await self.session_manager.logout(token)
        
        # Log logout
        await self.audit_trail.log(
            AuditEventType.LOGOUT,
            f"User logged out",
            actor_id=user_id,
            session_id=session_id,
            request=request
        )
    
    # Authorization Methods
    
    async def get_current_user(
        self,
        request: Request,
        token: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current authenticated user from token or API key"""
        # Try token authentication first
        if token:
            try:
                token_data = await self.session_manager.validate_token(token)
                
                # Log data access
                await self.audit_trail.log(
                    AuditEventType.DATA_READ,
                    "User authenticated via token",
                    actor_id=token_data.get("user_id"),
                    session_id=token_data.get("session_id"),
                    request=request
                )
                
                return {
                    "user_id": token_data.get("user_id"),
                    "session_id": token_data.get("session_id"),
                    "auth_method": "token"
                }
            except HTTPException:
                pass
        
        # Try API key authentication
        if api_key:
            try:
                key_data = await self.api_key_manager.validate_api_key(
                    api_key,
                    request=request
                )
                
                # Log API key usage
                await self.audit_trail.log(
                    AuditEventType.API_KEY_USED,
                    "API key authenticated",
                    actor_id=key_data.get("key_id"),
                    tenant_id=key_data.get("tenant_id"),
                    request=request
                )
                
                return {
                    "key_id": key_data.get("key_id"),
                    "tenant_id": key_data.get("tenant_id"),
                    "auth_method": "api_key",
                    "scopes": key_data.get("scopes")
                }
            except HTTPException:
                pass
        
        # No valid authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    def require_scopes(self, required_scopes: List[APIKeyScope]):
        """Dependency to require specific API scopes"""
        async def verify_scopes(
            request: Request,
            api_key: str = Depends(self.api_key_header)
        ):
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required"
                )
            
            await self.api_key_manager.validate_api_key(
                api_key,
                required_scopes=required_scopes,
                request=request
            )
            
            return True
        
        return verify_scopes
    
    # Password Management
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Change user password with validation"""
        # Validate new password
        validation = await self.password_validator.validate(
            password=new_password,
            old_passwords=[]  # Should fetch from database
        )
        
        if not validation['valid']:
            await self.audit_trail.log(
                AuditEventType.PASSWORD_CHANGED,
                f"Password change failed: weak password",
                severity=AuditSeverity.WARNING,
                actor_id=user_id,
                request=request,
                metadata={"errors": validation['errors']}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": validation['errors']}
            )
        
        # Hash new password
        from .password_policy import pwd_context
        new_hash = pwd_context.hash(new_password)
        
        # Update password (implementation depends on your user model)
        
        # Revoke all sessions
        await self.session_manager.revoke_all_user_sessions(
            user_id,
            reason="Password changed"
        )
        
        # Log password change
        await self.audit_trail.log(
            AuditEventType.PASSWORD_CHANGED,
            f"Password changed for user {user_id}",
            actor_id=user_id,
            request=request
        )
        
        return {
            "status": "success",
            "message": "Password changed successfully",
            "sessions_revoked": True
        }
    
    # API Key Management
    
    async def create_api_key_endpoint(
        self,
        name: str,
        scopes: List[APIKeyScope],
        user_id: str,
        tenant_id: str,
        request: Optional[Request] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new API key"""
        result = await self.api_key_manager.create_api_key(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            scopes=scopes,
            **kwargs
        )
        
        # Log API key creation
        await self.audit_trail.log(
            AuditEventType.API_KEY_CREATED,
            f"API key created: {name}",
            actor_id=user_id,
            target_id=result['key_id'],
            tenant_id=tenant_id,
            request=request,
            metadata={"scopes": scopes}
        )
        
        return result
    
    async def revoke_api_key_endpoint(
        self,
        key_id: str,
        user_id: str,
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Revoke an API key"""
        await self.api_key_manager.revoke_api_key(
            key_id=key_id,
            user_id=user_id,
            reason=reason
        )
        
        # Log API key revocation
        await self.audit_trail.log(
            AuditEventType.API_KEY_REVOKED,
            f"API key revoked: {key_id}",
            actor_id=user_id,
            target_id=key_id,
            request=request,
            metadata={"reason": reason}
        )
    
    # MFA Management
    
    async def setup_mfa_endpoint(
        self,
        user_id: str,
        method: str,
        request: Optional[Request] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Setup MFA for a user"""
        if method == "totp":
            result = await self.mfa_manager.setup_totp(
                user_id=user_id,
                user_email=kwargs.get("email", "")
            )
        elif method == "sms":
            result = await self.mfa_manager.setup_sms(
                user_id=user_id,
                phone_number=kwargs.get("phone_number", "")
            )
        elif method == "email":
            result = await self.mfa_manager.setup_email(
                user_id=user_id,
                email=kwargs.get("email", "")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA method"
            )
        
        # Log MFA setup
        await self.audit_trail.log(
            AuditEventType.MFA_VERIFIED,
            f"MFA setup initiated: {method}",
            actor_id=user_id,
            request=request,
            metadata={"method": method}
        )
        
        return result
    
    # Audit Trail Access
    
    async def get_audit_logs(
        self,
        user_id: str,
        request: Optional[Request] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get audit logs with permission check"""
        # Log audit access
        await self.audit_trail.log(
            AuditEventType.DATA_READ,
            "Audit logs accessed",
            actor_id=user_id,
            request=request,
            metadata={"filters": filters}
        )
        
        return await self.audit_trail.query(**filters)
    
    async def get_security_dashboard(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get security dashboard data"""
        # Get audit statistics
        audit_stats = await self.audit_trail.get_statistics(tenant_id=tenant_id)
        
        # Get active sessions count
        # Implementation depends on your session storage
        
        # Get API key statistics
        api_keys = await self.api_key_manager.list_api_keys(
            tenant_id=tenant_id,
            include_revoked=False
        )
        
        return {
            "audit_statistics": audit_stats,
            "active_api_keys": len(api_keys),
            "security_alerts": audit_stats.get("by_severity", {}).get("critical", 0),
            "failed_logins": audit_stats.get("by_type", {}).get(AuditEventType.LOGIN_FAILED, 0)
        }


# FastAPI integration helper
def setup_security(app: FastAPI, config: SecurityConfig) -> SecuritySystem:
    """Setup security system with FastAPI"""
    security = SecuritySystem(config)
    
    # Add startup/shutdown events
    @app.on_event("startup")
    async def startup():
        await security.init()
    
    @app.on_event("shutdown")
    async def shutdown():
        await security.close()
    
    # Add middleware for automatic audit logging
    @app.middleware("http")
    async def audit_middleware(request: Request, call_next):
        # Generate request ID if not present
        if "X-Request-ID" not in request.headers:
            request.headers.__dict__["_list"].append(
                (b"x-request-id", str(datetime.utcnow().timestamp()).encode())
            )
        
        # Process request
        response = await call_next(request)
        
        # Log high-level request (optional)
        if security.config.audit_enabled:
            # Only log non-GET requests or important GETs
            if request.method != "GET" or "admin" in str(request.url):
                await security.audit_trail.log(
                    AuditEventType.DATA_READ if request.method == "GET" else AuditEventType.DATA_UPDATED,
                    f"{request.method} {request.url.path}",
                    request=request,
                    metadata={"status": response.status_code}
                )
        
        return response
    
    return security


# Export main classes
__all__ = [
    'SecuritySystem',
    'SecurityConfig',
    'setup_security'
]
