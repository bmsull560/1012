"""
Security Module - OAuth2 + JWT + MFA Implementation
Implements production-grade authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import qrcode
import io
import base64
from fastapi import HTTPException, status

from .config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityService:
    """Handles authentication, authorization, and MFA"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60  # Convert to minutes
    
    # ============================================
    # Password Management
    # ============================================
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ============================================
    # JWT Token Management
    # ============================================
    
    def create_access_token(
        self, 
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            data: Payload to encode (user_id, email, tenant_id, etc.)
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow(),
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            data: Payload to encode
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.refresh_token_expire)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow(),
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise credentials_exception
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )
            
            return payload
            
        except JWTError:
            raise credentials_exception
    
    # ============================================
    # Multi-Factor Authentication (MFA)
    # ============================================
    
    def generate_mfa_secret(self) -> str:
        """
        Generate a new MFA secret for TOTP
        
        Returns:
            Base32-encoded secret
        """
        return pyotp.random_base32()
    
    def generate_mfa_qr_code(self, secret: str, user_email: str) -> str:
        """
        Generate QR code for MFA setup
        
        Args:
            secret: MFA secret
            user_email: User's email address
            
        Returns:
            Base64-encoded PNG image
        """
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="ValueVerse Platform"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """
        Verify TOTP token
        
        Args:
            secret: User's MFA secret
            token: 6-digit TOTP code
            
        Returns:
            True if valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 30s window
    
    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """
        Generate backup codes for MFA recovery
        
        Args:
            count: Number of backup codes to generate
            
        Returns:
            List of backup codes
        """
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    # ============================================
    # Session Management
    # ============================================
    
    def create_session_token(self, user_id: str, device_info: Dict[str, Any]) -> str:
        """
        Create a session token with device fingerprint
        
        Args:
            user_id: User ID
            device_info: Device information (IP, user agent, etc.)
            
        Returns:
            Session token
        """
        data = {
            "user_id": user_id,
            "device": device_info,
            "session_id": pyotp.random_base32()[:16],
        }
        return self.create_access_token(data, timedelta(hours=24))
    
    # ============================================
    # API Key Management
    # ============================================
    
    def generate_api_key(self, user_id: str, name: str, scopes: list[str]) -> str:
        """
        Generate API key for programmatic access
        
        Args:
            user_id: User ID
            name: API key name/description
            scopes: List of permission scopes
            
        Returns:
            API key
        """
        import secrets
        prefix = "vv_live" if settings.ENVIRONMENT == "production" else "vv_test"
        key = f"{prefix}_{secrets.token_urlsafe(32)}"
        
        # In production, store key hash and metadata in database
        # Here we're just generating the key
        return key
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Verify API key and return associated user/permissions
        
        Args:
            api_key: API key to verify
            
        Returns:
            User and permission data
            
        Raises:
            HTTPException: If API key is invalid
        """
        # In production, look up key in database
        # This is a placeholder implementation
        if not api_key.startswith("vv_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
            )
        
        # Return placeholder data
        return {
            "user_id": "system",
            "scopes": ["read", "write"],
            "rate_limit": settings.RATE_LIMIT_PER_HOUR,
        }


# Global security service instance
security = SecurityService()


# Dependency for FastAPI routes
def get_security_service() -> SecurityService:
    """Dependency injection for security service"""
    return security
