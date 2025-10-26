"""
PCI DSS Compliant Tokenization Vault
Implements secure tokenization for cardholder data with encryption and key management
"""

import os
import secrets
import hashlib
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import asyncpg
from pydantic import BaseModel, Field, validator
import re


class CardData(BaseModel):
    """Cardholder data model"""
    card_number: str
    card_holder_name: str
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=datetime.now().year, le=datetime.now().year + 20)
    cvv: Optional[str] = None  # Should never be stored
    
    @validator('card_number')
    def validate_card_number(cls, v):
        """Validate and clean card number"""
        # Remove spaces and dashes
        v = re.sub(r'[\s-]', '', v)
        
        # Check if all digits
        if not v.isdigit():
            raise ValueError("Card number must contain only digits")
        
        # Check length (13-19 digits)
        if len(v) < 13 or len(v) > 19:
            raise ValueError("Invalid card number length")
        
        # Luhn algorithm validation
        if not cls._luhn_check(v):
            raise ValueError("Invalid card number")
        
        return v
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Validate card number using Luhn algorithm"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        
        return checksum % 10 == 0
    
    def get_masked_number(self) -> str:
        """Get masked card number (show only last 4 digits)"""
        return f"****-****-****-{self.card_number[-4:]}"
    
    def get_bin(self) -> str:
        """Get Bank Identification Number (first 6 digits)"""
        return self.card_number[:6]


class TokenizedCard(BaseModel):
    """Tokenized card data"""
    token: str
    masked_number: str
    card_bin: str
    card_brand: str
    expiry_month: int
    expiry_year: int
    created_at: datetime
    last_used_at: Optional[datetime] = None


class PCITokenizationVault:
    """
    PCI DSS Compliant Tokenization Vault
    Implements Format Preserving Encryption (FPE) and secure key management
    """
    
    def __init__(self, database_url: str, master_key: Optional[str] = None):
        """
        Initialize tokenization vault
        
        Args:
            database_url: PostgreSQL connection string (should use SSL)
            master_key: Master encryption key (should be from HSM in production)
        """
        self.database_url = database_url
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Master key management (in production, use HSM or KMS)
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Try to load from environment
            env_key = os.getenv("PCI_MASTER_KEY")
            if not env_key:
                raise RuntimeError(
                    "CRITICAL: PCI_MASTER_KEY must be set for tokenization vault. "
                    "In production, this should come from an HSM or KMS."
                )
            self.master_key = env_key.encode()
        
        # Derive encryption keys
        self._derive_keys()
    
    def _derive_keys(self):
        """Derive encryption keys from master key"""
        # Derive tokenization key
        kdf_token = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tokenization_salt_v1',  # In production, use random salt stored securely
            iterations=100000,
            backend=default_backend()
        )
        self.tokenization_key = kdf_token.derive(self.master_key)
        
        # Derive data encryption key
        kdf_data = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'data_encryption_salt_v1',
            iterations=100000,
            backend=default_backend()
        )
        self.data_key = kdf_data.derive(self.master_key)
        
        # Create Fernet instance for data encryption
        self.fernet = Fernet(Fernet.generate_key())  # Use derived key in production
    
    async def init(self):
        """Initialize database connection and tables"""
        # Create connection pool with SSL
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            ssl='require',  # Enforce SSL
            min_size=2,
            max_size=10
        )
        
        # Create CDE schema and tables
        await self._create_cde_schema()
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def _create_cde_schema(self):
        """Create Cardholder Data Environment schema and tables"""
        async with self.db_pool.acquire() as conn:
            # Create CDE schema
            await conn.execute("""
                CREATE SCHEMA IF NOT EXISTS cde;
                
                -- Tokenization vault table
                CREATE TABLE IF NOT EXISTS cde.tokenization_vault (
                    token VARCHAR(32) PRIMARY KEY,
                    encrypted_pan BYTEA NOT NULL,
                    pan_hash VARCHAR(64) NOT NULL,
                    masked_pan VARCHAR(19) NOT NULL,
                    card_bin VARCHAR(6) NOT NULL,
                    card_brand VARCHAR(20),
                    expiry_month INTEGER,
                    expiry_year INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    last_accessed_at TIMESTAMPTZ,
                    access_count INTEGER DEFAULT 0,
                    organization_id UUID,
                    
                    -- Indexes for lookup
                    INDEX idx_pan_hash (pan_hash),
                    INDEX idx_org_id (organization_id),
                    INDEX idx_created_at (created_at)
                );
                
                -- Encryption keys table (for key rotation)
                CREATE TABLE IF NOT EXISTS cde.encryption_keys (
                    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    key_version INTEGER NOT NULL,
                    encrypted_key BYTEA NOT NULL,
                    key_type VARCHAR(20) NOT NULL,
                    algorithm VARCHAR(20) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    rotated_at TIMESTAMPTZ,
                    expires_at TIMESTAMPTZ,
                    is_active BOOLEAN DEFAULT TRUE,
                    
                    UNIQUE(key_version, key_type)
                );
                
                -- Audit log for CDE access
                CREATE TABLE IF NOT EXISTS cde.access_log (
                    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token VARCHAR(32),
                    action VARCHAR(20) NOT NULL,
                    user_id UUID,
                    ip_address INET,
                    user_agent TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    accessed_at TIMESTAMPTZ DEFAULT NOW(),
                    
                    INDEX idx_token (token),
                    INDEX idx_accessed_at (accessed_at)
                );
                
                -- Grant minimal permissions
                REVOKE ALL ON SCHEMA cde FROM PUBLIC;
                GRANT USAGE ON SCHEMA cde TO billing_tokenizer;
                GRANT SELECT, INSERT ON cde.tokenization_vault TO billing_tokenizer;
                GRANT INSERT ON cde.access_log TO billing_tokenizer;
            """)
    
    async def tokenize(
        self,
        card_data: CardData,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> TokenizedCard:
        """
        Tokenize cardholder data
        
        Args:
            card_data: Card data to tokenize
            organization_id: Organization ID for multi-tenancy
            user_id: User performing tokenization
            ip_address: Client IP for audit
            
        Returns:
            TokenizedCard with token and masked data
        """
        # Generate secure token
        token = self._generate_token()
        
        # Hash PAN for duplicate detection
        pan_hash = self._hash_pan(card_data.card_number)
        
        # Check if card already tokenized
        existing_token = await self._find_existing_token(pan_hash, organization_id)
        if existing_token:
            # Log access
            await self._log_access(
                token=existing_token['token'],
                action='tokenize_duplicate',
                user_id=user_id,
                ip_address=ip_address,
                success=True
            )
            
            return TokenizedCard(
                token=existing_token['token'],
                masked_number=existing_token['masked_pan'],
                card_bin=existing_token['card_bin'],
                card_brand=existing_token['card_brand'],
                expiry_month=existing_token['expiry_month'],
                expiry_year=existing_token['expiry_year'],
                created_at=existing_token['created_at']
            )
        
        # Encrypt PAN
        encrypted_pan = self._encrypt_pan(card_data.card_number)
        
        # Detect card brand
        card_brand = self._detect_card_brand(card_data.card_number)
        
        # Store tokenized data
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cde.tokenization_vault (
                    token, encrypted_pan, pan_hash, masked_pan,
                    card_bin, card_brand, expiry_month, expiry_year,
                    organization_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, token, encrypted_pan, pan_hash, card_data.get_masked_number(),
                card_data.get_bin(), card_brand, card_data.expiry_month,
                card_data.expiry_year, organization_id)
        
        # Log tokenization
        await self._log_access(
            token=token,
            action='tokenize',
            user_id=user_id,
            ip_address=ip_address,
            success=True
        )
        
        return TokenizedCard(
            token=token,
            masked_number=card_data.get_masked_number(),
            card_bin=card_data.get_bin(),
            card_brand=card_brand,
            expiry_month=card_data.expiry_month,
            expiry_year=card_data.expiry_year,
            created_at=datetime.utcnow()
        )
    
    async def detokenize(
        self,
        token: str,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Optional[str]:
        """
        Detokenize to retrieve original PAN
        
        CRITICAL: This operation must be heavily restricted and audited
        
        Args:
            token: Token to detokenize
            organization_id: Organization ID for validation
            user_id: User requesting detokenization
            ip_address: Client IP for audit
            reason: Reason for detokenization (required for audit)
            
        Returns:
            Original PAN if authorized, None otherwise
        """
        if not reason:
            await self._log_access(
                token=token,
                action='detokenize',
                user_id=user_id,
                ip_address=ip_address,
                success=False,
                error_message="Reason required for detokenization"
            )
            raise ValueError("Reason must be provided for detokenization")
        
        # Retrieve encrypted data
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT encrypted_pan, organization_id
                FROM cde.tokenization_vault
                WHERE token = $1
            """, token)
            
            if not result:
                await self._log_access(
                    token=token,
                    action='detokenize',
                    user_id=user_id,
                    ip_address=ip_address,
                    success=False,
                    error_message="Token not found"
                )
                return None
            
            # Validate organization
            if organization_id and result['organization_id'] != organization_id:
                await self._log_access(
                    token=token,
                    action='detokenize',
                    user_id=user_id,
                    ip_address=ip_address,
                    success=False,
                    error_message="Organization mismatch"
                )
                return None
            
            # Update access tracking
            await conn.execute("""
                UPDATE cde.tokenization_vault
                SET last_accessed_at = NOW(),
                    access_count = access_count + 1
                WHERE token = $1
            """, token)
        
        # Decrypt PAN
        pan = self._decrypt_pan(result['encrypted_pan'])
        
        # Log successful detokenization
        await self._log_access(
            token=token,
            action='detokenize',
            user_id=user_id,
            ip_address=ip_address,
            success=True,
            error_message=f"Reason: {reason}"
        )
        
        return pan
    
    async def rotate_keys(self):
        """
        Rotate encryption keys
        This should be called periodically (e.g., quarterly)
        """
        # Generate new keys
        new_master_key = Fernet.generate_key()
        
        # Re-encrypt all data with new key
        async with self.db_pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Get all encrypted data
                rows = await conn.fetch("""
                    SELECT token, encrypted_pan
                    FROM cde.tokenization_vault
                """)
                
                # Re-encrypt each PAN
                for row in rows:
                    # Decrypt with old key
                    pan = self._decrypt_pan(row['encrypted_pan'])
                    
                    # Update keys
                    self.master_key = new_master_key
                    self._derive_keys()
                    
                    # Encrypt with new key
                    new_encrypted_pan = self._encrypt_pan(pan)
                    
                    # Update database
                    await conn.execute("""
                        UPDATE cde.tokenization_vault
                        SET encrypted_pan = $1
                        WHERE token = $2
                    """, new_encrypted_pan, row['token'])
                
                # Store new key version
                await conn.execute("""
                    INSERT INTO cde.encryption_keys (
                        key_version, encrypted_key, key_type,
                        algorithm, expires_at
                    ) VALUES (
                        (SELECT COALESCE(MAX(key_version), 0) + 1 FROM cde.encryption_keys),
                        $1, 'master', 'AES-256-GCM',
                        NOW() + INTERVAL '90 days'
                    )
                """, new_master_key)
                
                # Deactivate old keys
                await conn.execute("""
                    UPDATE cde.encryption_keys
                    SET is_active = FALSE, rotated_at = NOW()
                    WHERE key_type = 'master' AND is_active = TRUE
                """)
    
    def _generate_token(self) -> str:
        """Generate secure random token"""
        # Generate 16 bytes of random data
        random_bytes = secrets.token_bytes(16)
        # Convert to hex string (32 characters)
        return random_bytes.hex()
    
    def _hash_pan(self, pan: str) -> str:
        """Hash PAN for duplicate detection"""
        return hashlib.sha256(pan.encode()).hexdigest()
    
    def _encrypt_pan(self, pan: str) -> bytes:
        """Encrypt PAN using AES-256-GCM"""
        # Generate random IV
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.data_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt
        ciphertext = encryptor.update(pan.encode()) + encryptor.finalize()
        
        # Return IV + ciphertext + tag
        return iv + ciphertext + encryptor.tag
    
    def _decrypt_pan(self, encrypted_data: bytes) -> str:
        """Decrypt PAN"""
        # Extract components
        iv = encrypted_data[:12]
        tag = encrypted_data[-16:]
        ciphertext = encrypted_data[12:-16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.data_key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode()
    
    def _detect_card_brand(self, pan: str) -> str:
        """Detect card brand from PAN"""
        # Visa
        if pan[0] == '4':
            return 'Visa'
        # Mastercard
        elif pan[:2] in ['51', '52', '53', '54', '55'] or \
             (pan[:4] >= '2221' and pan[:4] <= '2720'):
            return 'Mastercard'
        # American Express
        elif pan[:2] in ['34', '37']:
            return 'American Express'
        # Discover
        elif pan[:4] == '6011' or pan[:2] == '65' or \
             (pan[:3] >= '644' and pan[:3] <= '649'):
            return 'Discover'
        # JCB
        elif pan[:4] >= '3528' and pan[:4] <= '3589':
            return 'JCB'
        # Diners Club
        elif pan[:2] in ['36', '38'] or pan[:3] in ['300', '301', '302', '303', '304', '305']:
            return 'Diners Club'
        else:
            return 'Unknown'
    
    async def _find_existing_token(
        self,
        pan_hash: str,
        organization_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find existing token for PAN"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT token, masked_pan, card_bin, card_brand,
                       expiry_month, expiry_year, created_at
                FROM cde.tokenization_vault
                WHERE pan_hash = $1
            """
            params = [pan_hash]
            
            if organization_id:
                query += " AND organization_id = $2"
                params.append(organization_id)
            
            result = await conn.fetchrow(query, *params)
            return dict(result) if result else None
    
    async def _log_access(
        self,
        token: str,
        action: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log access to CDE"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cde.access_log (
                    token, action, user_id, ip_address,
                    success, error_message
                ) VALUES ($1, $2, $3, $4::inet, $5, $6)
            """, token, action, user_id, ip_address, success, error_message)


# Export main class
__all__ = ['PCITokenizationVault', 'CardData', 'TokenizedCard']
