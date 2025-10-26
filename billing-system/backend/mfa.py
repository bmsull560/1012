"""
Multi-Factor Authentication (MFA) Implementation
Supports TOTP, SMS, Email, and Backup Codes
"""

import os
import secrets
import qrcode
import io
import base64
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pyotp
import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel, Field, EmailStr, validator
from twilio.rest import Client as TwilioClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import hashlib


class MFAConfig(BaseModel):
    """Configuration for MFA"""
    totp_issuer: str = Field(default="ValueVerse", min_length=1, max_length=50)
    totp_digits: int = Field(default=6, ge=6, le=8)
    totp_period: int = Field(default=30, ge=15, le=60)
    totp_algorithm: str = Field(default="SHA1", pattern="^(SHA1|SHA256|SHA512)$")
    
    sms_enabled: bool = True
    sms_code_length: int = Field(default=6, ge=4, le=8)
    sms_code_expiry_minutes: int = Field(default=10, ge=5, le=30)
    sms_max_attempts: int = Field(default=3, ge=1, le=5)
    
    email_enabled: bool = True
    email_code_length: int = Field(default=6, ge=4, le=8)
    email_code_expiry_minutes: int = Field(default=15, ge=5, le=60)
    email_max_attempts: int = Field(default=3, ge=1, le=5)
    
    backup_codes_count: int = Field(default=10, ge=5, le=20)
    backup_code_length: int = Field(default=8, ge=6, le=12)
    
    require_mfa_for_admin: bool = True
    allow_multiple_methods: bool = True
    grace_period_days: int = Field(default=7, ge=0, le=30)


class MFAMethod(BaseModel):
    """MFA method model"""
    method_id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    user_id: str
    method_type: str = Field(..., pattern="^(totp|sms|email|backup)$")
    is_primary: bool = False
    is_verified: bool = False
    secret: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    backup_codes: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MFAChallenge(BaseModel):
    """MFA challenge model"""
    challenge_id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    user_id: str
    method_type: str
    code: Optional[str] = None
    expires_at: datetime
    attempts: int = Field(default=0)
    max_attempts: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verified_at: Optional[datetime] = None


class MFAManager:
    """
    Multi-Factor Authentication Manager
    Handles TOTP, SMS, Email, and Backup Codes
    """
    
    def __init__(
        self,
        redis_url: str,
        config: Optional[MFAConfig] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_from_number: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_email: Optional[str] = None
    ):
        """Initialize MFA manager"""
        self.redis_url = redis_url
        self.config = config or MFAConfig()
        self.redis_client: Optional[redis.Redis] = None
        
        # Twilio configuration for SMS
        self.twilio_client = None
        if twilio_account_sid and twilio_auth_token:
            self.twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)
            self.twilio_from_number = twilio_from_number
        
        # SMTP configuration for email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email
    
    async def init(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    # TOTP Methods
    
    async def setup_totp(
        self,
        user_id: str,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Setup TOTP for a user
        
        Args:
            user_id: User ID
            user_email: User email for QR code label
        
        Returns:
            Dictionary with secret, QR code, and backup codes
        """
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(
            secret,
            issuer=self.config.totp_issuer,
            digits=self.config.totp_digits,
            interval=self.config.totp_period,
            digest=getattr(hashlib, self.config.totp_algorithm.lower())
        )
        
        # Generate provisioning URI
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.config.totp_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert QR code to base64 image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        # Store MFA method (unverified)
        method = MFAMethod(
            user_id=user_id,
            method_type="totp",
            secret=secret,
            backup_codes=[self._hash_backup_code(code) for code in backup_codes],
            is_verified=False
        )
        
        await self._store_mfa_method(method)
        
        return {
            "method_id": method.method_id,
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "provisioning_uri": provisioning_uri,
            "backup_codes": backup_codes
        }
    
    async def verify_totp_setup(
        self,
        user_id: str,
        method_id: str,
        code: str
    ) -> bool:
        """
        Verify TOTP setup with user-provided code
        
        Args:
            user_id: User ID
            method_id: MFA method ID
            code: TOTP code to verify
        
        Returns:
            True if verification successful
        """
        # Get MFA method
        method = await self._get_mfa_method(user_id, method_id)
        if not method or method.get("method_type") != "totp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA method"
            )
        
        # Verify code
        secret = method.get("secret")
        if self._verify_totp_code(secret, code):
            # Mark as verified
            method["is_verified"] = True
            method["verified_at"] = datetime.utcnow().isoformat()
            await self._store_mfa_method(method)
            return True
        
        return False
    
    async def verify_totp(
        self,
        user_id: str,
        code: str
    ) -> bool:
        """
        Verify TOTP code for authentication
        
        Args:
            user_id: User ID
            code: TOTP code to verify
        
        Returns:
            True if verification successful
        """
        # Get user's TOTP methods
        methods = await self._get_user_mfa_methods(user_id, "totp")
        
        for method in methods:
            if method.get("is_verified"):
                secret = method.get("secret")
                if self._verify_totp_code(secret, code):
                    # Update last used
                    method["last_used_at"] = datetime.utcnow().isoformat()
                    await self._store_mfa_method(method)
                    return True
        
        return False
    
    def _verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(
            secret,
            digits=self.config.totp_digits,
            interval=self.config.totp_period,
            digest=getattr(hashlib, self.config.totp_algorithm.lower())
        )
        # Allow for time drift (1 period before/after)
        return totp.verify(code, valid_window=1)
    
    # SMS Methods
    
    async def setup_sms(
        self,
        user_id: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Setup SMS MFA for a user
        
        Args:
            user_id: User ID
            phone_number: Phone number for SMS
        
        Returns:
            Dictionary with method ID and status
        """
        if not self.config.sms_enabled or not self.twilio_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS MFA is not enabled"
            )
        
        # Validate phone number format
        if not self._validate_phone_number(phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Store MFA method (unverified)
        method = MFAMethod(
            user_id=user_id,
            method_type="sms",
            phone_number=phone_number,
            is_verified=False
        )
        
        await self._store_mfa_method(method)
        
        # Send verification code
        await self.send_sms_code(user_id, method.method_id)
        
        return {
            "method_id": method.method_id,
            "phone_number": self._mask_phone_number(phone_number),
            "status": "verification_code_sent"
        }
    
    async def send_sms_code(
        self,
        user_id: str,
        method_id: Optional[str] = None
    ) -> str:
        """
        Send SMS verification code
        
        Args:
            user_id: User ID
            method_id: Optional specific method ID
        
        Returns:
            Challenge ID
        """
        # Get SMS method
        if method_id:
            method = await self._get_mfa_method(user_id, method_id)
        else:
            methods = await self._get_user_mfa_methods(user_id, "sms")
            method = methods[0] if methods else None
        
        if not method or method.get("method_type") != "sms":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS MFA not configured"
            )
        
        phone_number = method.get("phone_number")
        
        # Generate code
        code = self._generate_numeric_code(self.config.sms_code_length)
        
        # Create challenge
        challenge = MFAChallenge(
            user_id=user_id,
            method_type="sms",
            code=self._hash_code(code),
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.sms_code_expiry_minutes),
            max_attempts=self.config.sms_max_attempts
        )
        
        await self._store_challenge(challenge)
        
        # Send SMS
        if self.twilio_client:
            try:
                message = self.twilio_client.messages.create(
                    body=f"Your ValueVerse verification code is: {code}",
                    from_=self.twilio_from_number,
                    to=phone_number
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send SMS: {str(e)}"
                )
        
        return challenge.challenge_id
    
    # Email Methods
    
    async def setup_email(
        self,
        user_id: str,
        email: str
    ) -> Dict[str, Any]:
        """
        Setup Email MFA for a user
        
        Args:
            user_id: User ID
            email: Email address
        
        Returns:
            Dictionary with method ID and status
        """
        if not self.config.email_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email MFA is not enabled"
            )
        
        # Store MFA method (unverified)
        method = MFAMethod(
            user_id=user_id,
            method_type="email",
            email=email,
            is_verified=False
        )
        
        await self._store_mfa_method(method)
        
        # Send verification code
        await self.send_email_code(user_id, method.method_id)
        
        return {
            "method_id": method.method_id,
            "email": self._mask_email(email),
            "status": "verification_code_sent"
        }
    
    async def send_email_code(
        self,
        user_id: str,
        method_id: Optional[str] = None
    ) -> str:
        """
        Send email verification code
        
        Args:
            user_id: User ID
            method_id: Optional specific method ID
        
        Returns:
            Challenge ID
        """
        # Get email method
        if method_id:
            method = await self._get_mfa_method(user_id, method_id)
        else:
            methods = await self._get_user_mfa_methods(user_id, "email")
            method = methods[0] if methods else None
        
        if not method or method.get("method_type") != "email":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email MFA not configured"
            )
        
        email = method.get("email")
        
        # Generate code
        code = self._generate_numeric_code(self.config.email_code_length)
        
        # Create challenge
        challenge = MFAChallenge(
            user_id=user_id,
            method_type="email",
            code=self._hash_code(code),
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.email_code_expiry_minutes),
            max_attempts=self.config.email_max_attempts
        )
        
        await self._store_challenge(challenge)
        
        # Send email
        await self._send_email_code(email, code)
        
        return challenge.challenge_id
    
    async def _send_email_code(self, email: str, code: str):
        """Send email with verification code"""
        if not self.smtp_host:
            # Log the code for development
            print(f"Email verification code for {email}: {code}")
            return
        
        # Create message
        message = MIMEMultipart()
        message["From"] = self.smtp_from_email
        message["To"] = email
        message["Subject"] = "ValueVerse Verification Code"
        
        body = f"""
        Your ValueVerse verification code is: {code}
        
        This code will expire in {self.config.email_code_expiry_minutes} minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        try:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
    
    # Backup Codes
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(self.config.backup_codes_count):
            code = ''.join(
                secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                for _ in range(self.config.backup_code_length)
            )
            # Format with dashes for readability
            if self.config.backup_code_length >= 8:
                code = f"{code[:4]}-{code[4:]}"
            codes.append(code)
        return codes
    
    async def verify_backup_code(
        self,
        user_id: str,
        code: str
    ) -> bool:
        """
        Verify and consume a backup code
        
        Args:
            user_id: User ID
            code: Backup code to verify
        
        Returns:
            True if verification successful
        """
        # Remove formatting
        code = code.replace("-", "")
        
        # Get user's MFA methods
        methods = await self._get_user_mfa_methods(user_id)
        
        for method in methods:
            backup_codes = method.get("backup_codes", [])
            code_hash = self._hash_backup_code(code)
            
            if code_hash in backup_codes:
                # Remove used code
                backup_codes.remove(code_hash)
                method["backup_codes"] = backup_codes
                method["last_used_at"] = datetime.utcnow().isoformat()
                await self._store_mfa_method(method)
                return True
        
        return False
    
    async def regenerate_backup_codes(
        self,
        user_id: str
    ) -> List[str]:
        """
        Regenerate backup codes for a user
        
        Args:
            user_id: User ID
        
        Returns:
            New backup codes
        """
        # Generate new codes
        new_codes = self._generate_backup_codes()
        
        # Update all MFA methods with new backup codes
        methods = await self._get_user_mfa_methods(user_id)
        for method in methods:
            method["backup_codes"] = [
                self._hash_backup_code(code) for code in new_codes
            ]
            await self._store_mfa_method(method)
        
        return new_codes
    
    # Verification Methods
    
    async def verify_code(
        self,
        challenge_id: str,
        code: str
    ) -> bool:
        """
        Verify a challenge code (SMS or Email)
        
        Args:
            challenge_id: Challenge ID
            code: Code to verify
        
        Returns:
            True if verification successful
        """
        # Get challenge
        challenge = await self._get_challenge(challenge_id)
        if not challenge:
            return False
        
        # Check expiry
        expires_at = datetime.fromisoformat(challenge.get("expires_at"))
        if datetime.utcnow() > expires_at:
            await self._delete_challenge(challenge_id)
            return False
        
        # Check attempts
        attempts = challenge.get("attempts", 0)
        max_attempts = challenge.get("max_attempts", 3)
        if attempts >= max_attempts:
            await self._delete_challenge(challenge_id)
            return False
        
        # Verify code
        stored_code = challenge.get("code")
        if self._verify_code_hash(code, stored_code):
            # Mark as verified
            challenge["verified"] = True
            challenge["verified_at"] = datetime.utcnow().isoformat()
            await self._store_challenge(challenge)
            
            # Mark MFA method as verified if this was setup
            user_id = challenge.get("user_id")
            method_type = challenge.get("method_type")
            methods = await self._get_user_mfa_methods(user_id, method_type)
            for method in methods:
                if not method.get("is_verified"):
                    method["is_verified"] = True
                    method["verified_at"] = datetime.utcnow().isoformat()
                    await self._store_mfa_method(method)
            
            return True
        else:
            # Increment attempts
            challenge["attempts"] = attempts + 1
            await self._store_challenge(challenge)
            return False
    
    # User MFA Management
    
    async def get_user_mfa_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get MFA status for a user
        
        Args:
            user_id: User ID
        
        Returns:
            MFA status dictionary
        """
        methods = await self._get_user_mfa_methods(user_id)
        
        return {
            "mfa_enabled": len(methods) > 0,
            "methods": [
                {
                    "method_id": method.get("method_id"),
                    "method_type": method.get("method_type"),
                    "is_primary": method.get("is_primary", False),
                    "is_verified": method.get("is_verified", False),
                    "created_at": method.get("created_at"),
                    "last_used_at": method.get("last_used_at")
                }
                for method in methods
            ],
            "require_mfa": await self._check_mfa_requirement(user_id)
        }
    
    async def disable_mfa_method(
        self,
        user_id: str,
        method_id: str
    ):
        """Disable an MFA method"""
        await self._delete_mfa_method(user_id, method_id)
    
    # Helper Methods
    
    def _generate_numeric_code(self, length: int) -> str:
        """Generate numeric code"""
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    def _hash_code(self, code: str) -> str:
        """Hash a code for storage"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _verify_code_hash(self, code: str, hash: str) -> bool:
        """Verify a code against its hash"""
        return self._hash_code(code) == hash
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash a backup code"""
        # Remove formatting
        code = code.replace("-", "")
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        # Basic validation - in production use a library like phonenumbers
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))
    
    def _mask_phone_number(self, phone: str) -> str:
        """Mask phone number for display"""
        if len(phone) < 4:
            return "***"
        return f"***{phone[-4:]}"
    
    def _mask_email(self, email: str) -> str:
        """Mask email for display"""
        parts = email.split("@")
        if len(parts) != 2:
            return "***"
        username = parts[0]
        domain = parts[1]
        if len(username) <= 2:
            masked_username = "*" * len(username)
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
        return f"{masked_username}@{domain}"
    
    # Redis Storage Methods
    
    async def _store_mfa_method(self, method: Union[MFAMethod, Dict[str, Any]]):
        """Store MFA method in Redis"""
        if isinstance(method, MFAMethod):
            method_dict = method.dict()
        else:
            method_dict = method
        
        # Convert datetime objects
        for key in ["created_at", "verified_at", "last_used_at"]:
            if key in method_dict and isinstance(method_dict[key], datetime):
                method_dict[key] = method_dict[key].isoformat()
        
        user_id = method_dict.get("user_id")
        method_id = method_dict.get("method_id")
        
        # Store method
        await self.redis_client.hset(
            f"mfa:user:{user_id}",
            method_id,
            json.dumps(method_dict)
        )
    
    async def _get_mfa_method(
        self,
        user_id: str,
        method_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific MFA method"""
        data = await self.redis_client.hget(f"mfa:user:{user_id}", method_id)
        if data:
            return json.loads(data)
        return None
    
    async def _get_user_mfa_methods(
        self,
        user_id: str,
        method_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all MFA methods for a user"""
        methods_data = await self.redis_client.hgetall(f"mfa:user:{user_id}")
        methods = []
        
        for method_data in methods_data.values():
            method = json.loads(method_data)
            if not method_type or method.get("method_type") == method_type:
                methods.append(method)
        
        return methods
    
    async def _delete_mfa_method(self, user_id: str, method_id: str):
        """Delete an MFA method"""
        await self.redis_client.hdel(f"mfa:user:{user_id}", method_id)
    
    async def _store_challenge(self, challenge: Union[MFAChallenge, Dict[str, Any]]):
        """Store MFA challenge"""
        if isinstance(challenge, MFAChallenge):
            challenge_dict = challenge.dict()
        else:
            challenge_dict = challenge
        
        # Convert datetime objects
        for key in ["created_at", "expires_at", "verified_at"]:
            if key in challenge_dict and isinstance(challenge_dict[key], datetime):
                challenge_dict[key] = challenge_dict[key].isoformat()
        
        challenge_id = challenge_dict.get("challenge_id")
        expires_at = datetime.fromisoformat(challenge_dict.get("expires_at"))
        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        
        if ttl > 0:
            await self.redis_client.setex(
                f"mfa:challenge:{challenge_id}",
                ttl,
                json.dumps(challenge_dict)
            )
    
    async def _get_challenge(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """Get MFA challenge"""
        data = await self.redis_client.get(f"mfa:challenge:{challenge_id}")
        if data:
            return json.loads(data)
        return None
    
    async def _delete_challenge(self, challenge_id: str):
        """Delete MFA challenge"""
        await self.redis_client.delete(f"mfa:challenge:{challenge_id}")
    
    async def _check_mfa_requirement(self, user_id: str) -> bool:
        """Check if MFA is required for user"""
        # Check if user is admin (would need user role from database)
        # For now, return config setting
        return self.config.require_mfa_for_admin


# Export main classes
__all__ = [
    'MFAManager',
    'MFAConfig',
    'MFAMethod',
    'MFAChallenge'
]
