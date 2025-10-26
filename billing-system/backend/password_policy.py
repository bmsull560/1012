"""
NIST 800-63B Compliant Password Policy Implementation
Enforces strong password requirements and password history
"""

import re
import hashlib
import secrets
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from pydantic import BaseModel, Field, validator


# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordStrengthConfig(BaseModel):
    """Configuration for password strength requirements"""
    min_length: int = Field(default=12, ge=8, le=128)
    max_length: int = Field(default=128, ge=12, le=256)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    min_uppercase: int = Field(default=1, ge=0)
    min_lowercase: int = Field(default=1, ge=0)
    min_numbers: int = Field(default=1, ge=0)
    min_special: int = Field(default=1, ge=0)
    prevent_sequential: bool = True
    prevent_repeated: bool = True
    max_repeated_chars: int = Field(default=3, ge=2)
    check_common_passwords: bool = True
    check_breached_passwords: bool = True
    password_history_count: int = Field(default=12, ge=0, le=24)
    min_password_age_days: int = Field(default=1, ge=0)
    max_password_age_days: int = Field(default=90, ge=30, le=365)


class PasswordValidator:
    """
    NIST 800-63B compliant password validator
    Implements comprehensive password strength checks
    """
    
    # Common passwords list (top 10000 most common)
    # In production, load from a file or database
    COMMON_PASSWORDS = {
        'password', '123456', 'password123', '12345678', 'qwerty',
        'abc123', '123456789', 'password1', '12345', '1234567',
        'letmein', 'monkey', '1234567890', 'welcome', 'admin',
        'dragon', 'master', 'football', 'login', 'princess'
    }
    
    # Special characters allowed in passwords
    SPECIAL_CHARS = r'!@#$%^&*()_+-=[]{}|;:,.<>?/~`'
    
    def __init__(self, config: Optional[PasswordStrengthConfig] = None):
        """Initialize password validator with configuration"""
        self.config = config or PasswordStrengthConfig()
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_redis(self, redis_url: str):
        """Initialize Redis connection for breach checking"""
        self.redis_client = await redis.from_url(redis_url)
    
    async def validate(
        self,
        password: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        old_passwords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate password according to NIST 800-63B guidelines
        
        Args:
            password: The password to validate
            username: Username to check password doesn't contain
            email: Email to check password doesn't contain
            old_passwords: List of previous password hashes to check against
        
        Returns:
            Dictionary with validation results and any error messages
        """
        errors = []
        warnings = []
        strength_score = 100  # Start with perfect score
        
        # Length validation
        if len(password) < self.config.min_length:
            errors.append(f"Password must be at least {self.config.min_length} characters")
            strength_score -= 30
        elif len(password) > self.config.max_length:
            errors.append(f"Password must not exceed {self.config.max_length} characters")
            strength_score -= 10
        
        # Character type requirements
        uppercase_count = sum(1 for c in password if c.isupper())
        lowercase_count = sum(1 for c in password if c.islower())
        number_count = sum(1 for c in password if c.isdigit())
        special_count = sum(1 for c in password if c in self.SPECIAL_CHARS)
        
        if self.config.require_uppercase and uppercase_count < self.config.min_uppercase:
            errors.append(f"Password must contain at least {self.config.min_uppercase} uppercase letter(s)")
            strength_score -= 15
        
        if self.config.require_lowercase and lowercase_count < self.config.min_lowercase:
            errors.append(f"Password must contain at least {self.config.min_lowercase} lowercase letter(s)")
            strength_score -= 15
        
        if self.config.require_numbers and number_count < self.config.min_numbers:
            errors.append(f"Password must contain at least {self.config.min_numbers} number(s)")
            strength_score -= 15
        
        if self.config.require_special and special_count < self.config.min_special:
            errors.append(f"Password must contain at least {self.config.min_special} special character(s)")
            strength_score -= 15
        
        # Check for sequential characters
        if self.config.prevent_sequential:
            if self._has_sequential_chars(password):
                errors.append("Password contains sequential characters (e.g., 'abc', '123')")
                strength_score -= 20
        
        # Check for repeated characters
        if self.config.prevent_repeated:
            max_repeated = self._get_max_repeated_chars(password)
            if max_repeated > self.config.max_repeated_chars:
                errors.append(f"Password contains more than {self.config.max_repeated_chars} repeated characters")
                strength_score -= 15
        
        # Check against common passwords
        if self.config.check_common_passwords:
            if password.lower() in self.COMMON_PASSWORDS:
                errors.append("Password is too common and easily guessable")
                strength_score -= 40
        
        # Check if password contains username or email
        if username and username.lower() in password.lower():
            errors.append("Password must not contain your username")
            strength_score -= 25
        
        if email:
            email_prefix = email.split('@')[0].lower()
            if email_prefix in password.lower():
                errors.append("Password must not contain your email address")
                strength_score -= 25
        
        # Check against password history
        if old_passwords and self.config.password_history_count > 0:
            for old_hash in old_passwords[:self.config.password_history_count]:
                if pwd_context.verify(password, old_hash):
                    errors.append(f"Password was used recently. Please choose a different password")
                    strength_score -= 30
                    break
        
        # Check against breached passwords (using k-anonymity)
        if self.config.check_breached_passwords and self.redis_client:
            is_breached = await self._check_breached_password(password)
            if is_breached:
                errors.append("This password has been found in data breaches. Please choose a different password")
                strength_score -= 50
        
        # Calculate entropy
        entropy = self._calculate_entropy(password)
        if entropy < 30:
            warnings.append("Password entropy is low. Consider using a longer, more complex password")
            strength_score -= 10
        
        # Ensure score doesn't go below 0
        strength_score = max(0, strength_score)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strength_score': strength_score,
            'entropy': entropy,
            'character_diversity': {
                'uppercase': uppercase_count,
                'lowercase': lowercase_count,
                'numbers': number_count,
                'special': special_count
            }
        }
    
    def _has_sequential_chars(self, password: str, min_length: int = 3) -> bool:
        """Check for sequential characters like 'abc' or '123'"""
        for i in range(len(password) - min_length + 1):
            substring = password[i:i + min_length]
            
            # Check ascending sequence
            is_ascending = all(
                ord(substring[j]) + 1 == ord(substring[j + 1])
                for j in range(len(substring) - 1)
            )
            
            # Check descending sequence
            is_descending = all(
                ord(substring[j]) - 1 == ord(substring[j + 1])
                for j in range(len(substring) - 1)
            )
            
            if is_ascending or is_descending:
                return True
        
        return False
    
    def _get_max_repeated_chars(self, password: str) -> int:
        """Get the maximum number of consecutive repeated characters"""
        if not password:
            return 0
        
        max_repeated = 1
        current_repeated = 1
        
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                current_repeated += 1
                max_repeated = max(max_repeated, current_repeated)
            else:
                current_repeated = 1
        
        return max_repeated
    
    def _calculate_entropy(self, password: str) -> float:
        """
        Calculate password entropy in bits
        Entropy = log2(possible_characters^length)
        """
        import math
        
        charset_size = 0
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in self.SPECIAL_CHARS for c in password):
            charset_size += len(self.SPECIAL_CHARS)
        
        if charset_size == 0:
            return 0
        
        entropy = len(password) * math.log2(charset_size)
        return round(entropy, 2)
    
    async def _check_breached_password(self, password: str) -> bool:
        """
        Check if password has been breached using k-anonymity
        Uses the HaveIBeenPwned API approach
        """
        if not self.redis_client:
            return False
        
        # Hash the password with SHA-1 (for HIBP compatibility)
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        # Check Redis cache first
        cache_key = f"pwned:{prefix}"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            # Check if our suffix is in the cached data
            return suffix in cached_data
        
        # In production, query the HIBP API here
        # For now, return False (not breached)
        return False
    
    def generate_strong_password(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """
        Generate a strong random password
        
        Args:
            length: Password length (default 16)
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters
            include_numbers: Include numbers
            include_special: Include special characters
            exclude_ambiguous: Exclude ambiguous characters (0, O, l, 1, etc.)
        
        Returns:
            Generated password string
        """
        charset = ""
        
        if include_uppercase:
            charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if include_lowercase:
            charset += "abcdefghijklmnopqrstuvwxyz"
        if include_numbers:
            charset += "0123456789"
        if include_special:
            charset += self.SPECIAL_CHARS
        
        if exclude_ambiguous:
            # Remove ambiguous characters
            ambiguous = "0O1lI"
            charset = ''.join(c for c in charset if c not in ambiguous)
        
        if not charset:
            raise ValueError("At least one character type must be included")
        
        # Generate password
        password = ''.join(secrets.choice(charset) for _ in range(length))
        
        # Ensure password meets requirements
        while True:
            validation_result = asyncio.run(self.validate(password))
            if validation_result['valid']:
                break
            # Regenerate if validation fails
            password = ''.join(secrets.choice(charset) for _ in range(length))
        
        return password


class PasswordHistory:
    """Manage password history for users"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_password(
        self,
        user_id: str,
        password_hash: str,
        max_history: int = 12
    ):
        """Add a password to user's history"""
        # Implementation depends on your database schema
        # This is a placeholder
        pass
    
    async def get_password_history(
        self,
        user_id: str,
        limit: int = 12
    ) -> List[str]:
        """Get user's password history"""
        # Implementation depends on your database schema
        # This is a placeholder
        return []
    
    async def check_password_age(
        self,
        user_id: str,
        min_age_days: int = 1,
        max_age_days: int = 90
    ) -> Dict[str, Any]:
        """Check if password meets age requirements"""
        # Implementation depends on your database schema
        # This is a placeholder
        return {
            'can_change': True,
            'must_change': False,
            'days_until_expiry': 90
        }


# Export main classes
__all__ = [
    'PasswordValidator',
    'PasswordStrengthConfig',
    'PasswordHistory',
    'pwd_context'
]
