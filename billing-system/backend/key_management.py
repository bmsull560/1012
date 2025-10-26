"""
Secure Key Management System with Rotation
Implements enterprise-grade key management with HSM support and automatic rotation
"""

import os
import json
import secrets
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import asyncpg
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import redis.asyncio as redis
from pydantic import BaseModel, Field


class KeyType(str, Enum):
    """Types of encryption keys"""
    MASTER = "master"
    DATA_ENCRYPTION = "data_encryption"
    TOKEN_SIGNING = "token_signing"
    PCI_TOKENIZATION = "pci_tokenization"
    AUDIT_SIGNING = "audit_signing"
    API_KEY = "api_key"


class KeyStatus(str, Enum):
    """Key lifecycle status"""
    PENDING = "pending"
    ACTIVE = "active"
    ROTATING = "rotating"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ARCHIVED = "archived"


class EncryptionKey(BaseModel):
    """Encryption key model"""
    key_id: str = Field(default_factory=lambda: str(uuid4()))
    key_type: KeyType
    key_version: int
    algorithm: str = "AES-256-GCM"
    key_material: Optional[bytes] = None  # Encrypted
    public_key: Optional[str] = None  # For asymmetric keys
    created_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    status: KeyStatus = KeyStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None


class SecureKeyManagementSystem:
    """
    Enterprise-grade key management system with HSM support
    Implements key rotation, versioning, and secure storage
    """
    
    def __init__(
        self,
        database_url: str,
        redis_url: str = "redis://localhost:6379",
        hsm_enabled: bool = False,
        hsm_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize key management system
        
        Args:
            database_url: PostgreSQL connection string
            redis_url: Redis connection for key caching
            hsm_enabled: Whether to use Hardware Security Module
            hsm_config: HSM configuration if enabled
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.hsm_enabled = hsm_enabled
        self.hsm_config = hsm_config or {}
        
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Master key for key encryption (KEK - Key Encryption Key)
        self._load_or_create_kek()
        
        # Key cache for performance
        self._key_cache: Dict[str, EncryptionKey] = {}
        
        # Rotation schedule (days)
        self.rotation_schedule = {
            KeyType.MASTER: 365,  # Yearly
            KeyType.DATA_ENCRYPTION: 90,  # Quarterly
            KeyType.TOKEN_SIGNING: 30,  # Monthly
            KeyType.PCI_TOKENIZATION: 90,  # Quarterly (PCI requirement)
            KeyType.AUDIT_SIGNING: 180,  # Semi-annually
            KeyType.API_KEY: 90,  # Quarterly
        }
    
    def _load_or_create_kek(self):
        """Load or create Key Encryption Key (KEK)"""
        kek_env = os.getenv("KEY_ENCRYPTION_KEY")
        
        if self.hsm_enabled:
            # In production, use HSM for KEK
            self.kek = self._get_kek_from_hsm()
        elif kek_env:
            # Use provided KEK
            self.kek = kek_env.encode()
        else:
            # CRITICAL: Must fail in production without KEK
            if os.getenv("ENVIRONMENT") == "production":
                raise RuntimeError(
                    "CRITICAL: KEY_ENCRYPTION_KEY must be set in production. "
                    "This is the master key for all other keys."
                )
            # Development only - generate KEK
            self.kek = Fernet.generate_key()
            print(f"WARNING: Generated development KEK. Set KEY_ENCRYPTION_KEY for production.")
    
    def _get_kek_from_hsm(self) -> bytes:
        """Retrieve KEK from Hardware Security Module"""
        # Placeholder for HSM integration
        # In production, integrate with AWS KMS, Azure Key Vault, or HashiCorp Vault
        raise NotImplementedError("HSM integration required for production")
    
    async def init(self):
        """Initialize database and Redis connections"""
        # Initialize database pool
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        
        # Initialize Redis
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=False)
        
        # Create key management schema
        await self._create_schema()
        
        # Initialize default keys
        await self._initialize_default_keys()
        
        # Start rotation scheduler
        await self._schedule_rotations()
    
    async def close(self):
        """Close connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def _create_schema(self):
        """Create key management database schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                -- Key management schema
                CREATE SCHEMA IF NOT EXISTS key_management;
                
                -- Encryption keys table
                CREATE TABLE IF NOT EXISTS key_management.encryption_keys (
                    key_id UUID PRIMARY KEY,
                    key_type VARCHAR(50) NOT NULL,
                    key_version INTEGER NOT NULL,
                    algorithm VARCHAR(50) NOT NULL,
                    encrypted_key_material BYTEA NOT NULL,
                    public_key TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    activated_at TIMESTAMPTZ,
                    expires_at TIMESTAMPTZ,
                    rotated_at TIMESTAMPTZ,
                    status VARCHAR(20) NOT NULL,
                    metadata JSONB,
                    
                    -- Ensure unique version per key type
                    UNIQUE(key_type, key_version),
                    
                    -- Indexes
                    INDEX idx_key_type (key_type),
                    INDEX idx_status (status),
                    INDEX idx_expires (expires_at)
                );
                
                -- Key rotation log
                CREATE TABLE IF NOT EXISTS key_management.rotation_log (
                    rotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    key_type VARCHAR(50) NOT NULL,
                    old_key_id UUID,
                    new_key_id UUID,
                    rotated_at TIMESTAMPTZ DEFAULT NOW(),
                    rotated_by VARCHAR(100),
                    reason TEXT,
                    success BOOLEAN,
                    error_message TEXT
                );
                
                -- Key usage audit
                CREATE TABLE IF NOT EXISTS key_management.key_usage_audit (
                    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    key_id UUID NOT NULL,
                    operation VARCHAR(50) NOT NULL,
                    performed_at TIMESTAMPTZ DEFAULT NOW(),
                    performed_by VARCHAR(100),
                    ip_address INET,
                    success BOOLEAN,
                    metadata JSONB
                );
                
                -- Function to rotate encryption keys
                CREATE OR REPLACE FUNCTION key_management.fn_rotate_encryption_keys(
                    p_key_type VARCHAR,
                    p_reason TEXT DEFAULT 'Scheduled rotation'
                ) RETURNS UUID AS $$
                DECLARE
                    v_old_key_id UUID;
                    v_new_key_id UUID;
                    v_new_version INTEGER;
                BEGIN
                    -- Get current active key
                    SELECT key_id INTO v_old_key_id
                    FROM key_management.encryption_keys
                    WHERE key_type = p_key_type
                    AND status = 'active'
                    ORDER BY key_version DESC
                    LIMIT 1;
                    
                    -- Calculate new version
                    SELECT COALESCE(MAX(key_version), 0) + 1 INTO v_new_version
                    FROM key_management.encryption_keys
                    WHERE key_type = p_key_type;
                    
                    -- New key will be created by application
                    v_new_key_id := gen_random_uuid();
                    
                    -- Mark old key as rotating
                    IF v_old_key_id IS NOT NULL THEN
                        UPDATE key_management.encryption_keys
                        SET status = 'rotating',
                            rotated_at = NOW()
                        WHERE key_id = v_old_key_id;
                    END IF;
                    
                    -- Log rotation
                    INSERT INTO key_management.rotation_log (
                        key_type, old_key_id, new_key_id, reason, success
                    ) VALUES (
                        p_key_type, v_old_key_id, v_new_key_id, p_reason, TRUE
                    );
                    
                    RETURN v_new_key_id;
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
                
                -- Grant minimal permissions
                REVOKE ALL ON SCHEMA key_management FROM PUBLIC;
                GRANT USAGE ON SCHEMA key_management TO billing_app;
                GRANT SELECT, INSERT, UPDATE ON key_management.encryption_keys TO billing_app;
                GRANT INSERT ON key_management.rotation_log TO billing_app;
                GRANT INSERT ON key_management.key_usage_audit TO billing_app;
            """)
    
    async def _initialize_default_keys(self):
        """Initialize default keys for each type if not present"""
        for key_type in KeyType:
            # Check if key exists
            existing = await self.get_active_key(key_type)
            if not existing:
                # Create initial key
                await self.create_key(key_type)
    
    async def create_key(
        self,
        key_type: KeyType,
        algorithm: str = "AES-256-GCM"
    ) -> EncryptionKey:
        """
        Create a new encryption key
        
        Args:
            key_type: Type of key to create
            algorithm: Encryption algorithm
            
        Returns:
            Created encryption key
        """
        # Generate key material based on type
        if key_type in [KeyType.TOKEN_SIGNING, KeyType.AUDIT_SIGNING]:
            # Asymmetric key for signing
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            key_material = private_pem
            public_key_str = public_pem.decode()
        else:
            # Symmetric key for encryption
            key_material = os.urandom(32)  # 256 bits
            public_key_str = None
        
        # Encrypt key material with KEK
        encrypted_material = self._encrypt_key_material(key_material)
        
        # Get next version number
        async with self.db_pool.acquire() as conn:
            version = await conn.fetchval("""
                SELECT COALESCE(MAX(key_version), 0) + 1
                FROM key_management.encryption_keys
                WHERE key_type = $1
            """, key_type.value)
        
        # Create key object
        key = EncryptionKey(
            key_type=key_type,
            key_version=version,
            algorithm=algorithm,
            key_material=encrypted_material,
            public_key=public_key_str,
            status=KeyStatus.ACTIVE,
            activated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.rotation_schedule[key_type])
        )
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO key_management.encryption_keys (
                    key_id, key_type, key_version, algorithm,
                    encrypted_key_material, public_key, status,
                    activated_at, expires_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, UUID(key.key_id), key.key_type.value, key.key_version,
                key.algorithm, encrypted_material, key.public_key,
                key.status.value, key.activated_at, key.expires_at,
                json.dumps(key.metadata) if key.metadata else None)
        
        # Cache the key
        await self._cache_key(key)
        
        # Log key creation
        await self._audit_key_operation(key.key_id, "create", True)
        
        return key
    
    async def rotate_key(
        self,
        key_type: KeyType,
        reason: str = "Scheduled rotation"
    ) -> Tuple[EncryptionKey, EncryptionKey]:
        """
        Rotate an encryption key
        
        Args:
            key_type: Type of key to rotate
            reason: Reason for rotation
            
        Returns:
            Tuple of (old_key, new_key)
        """
        # Get current active key
        old_key = await self.get_active_key(key_type)
        if not old_key:
            raise ValueError(f"No active key found for type {key_type}")
        
        # Create new key
        new_key = await self.create_key(key_type)
        
        # Mark old key as rotating
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE key_management.encryption_keys
                SET status = $1, rotated_at = $2
                WHERE key_id = $3
            """, KeyStatus.ROTATING.value, datetime.utcnow(), UUID(old_key.key_id))
        
        # Log rotation
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO key_management.rotation_log (
                    key_type, old_key_id, new_key_id, reason, success
                ) VALUES ($1, $2, $3, $4, TRUE)
            """, key_type.value, UUID(old_key.key_id), UUID(new_key.key_id), reason)
        
        # Re-encrypt data with new key (application-specific)
        # This would be handled by the specific service using the key
        
        # Schedule old key expiration
        await self._schedule_key_expiration(old_key.key_id, days=30)
        
        return old_key, new_key
    
    async def get_active_key(self, key_type: KeyType) -> Optional[EncryptionKey]:
        """
        Get the current active key for a type
        
        Args:
            key_type: Type of key to retrieve
            
        Returns:
            Active encryption key or None
        """
        # Check cache first
        cache_key = f"active_key:{key_type.value}"
        cached = await self.redis_client.get(cache_key)
        if cached:
            return EncryptionKey.parse_raw(cached)
        
        # Query database
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM key_management.encryption_keys
                WHERE key_type = $1 AND status = $2
                ORDER BY key_version DESC
                LIMIT 1
            """, key_type.value, KeyStatus.ACTIVE.value)
            
            if not row:
                return None
            
            key = EncryptionKey(
                key_id=str(row['key_id']),
                key_type=key_type,
                key_version=row['key_version'],
                algorithm=row['algorithm'],
                key_material=row['encrypted_key_material'],
                public_key=row['public_key'],
                created_at=row['created_at'],
                activated_at=row['activated_at'],
                expires_at=row['expires_at'],
                status=KeyStatus(row['status'])
            )
            
            # Cache the key
            await self._cache_key(key)
            
            return key
    
    async def get_key_by_version(
        self,
        key_type: KeyType,
        version: int
    ) -> Optional[EncryptionKey]:
        """Get a specific version of a key"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM key_management.encryption_keys
                WHERE key_type = $1 AND key_version = $2
            """, key_type.value, version)
            
            if not row:
                return None
            
            return EncryptionKey(
                key_id=str(row['key_id']),
                key_type=key_type,
                key_version=row['key_version'],
                algorithm=row['algorithm'],
                key_material=row['encrypted_key_material'],
                public_key=row['public_key'],
                created_at=row['created_at'],
                activated_at=row['activated_at'],
                expires_at=row['expires_at'],
                status=KeyStatus(row['status'])
            )
    
    def decrypt_key_material(self, encrypted_material: bytes) -> bytes:
        """Decrypt key material using KEK"""
        fernet = Fernet(self.kek)
        return fernet.decrypt(encrypted_material)
    
    def _encrypt_key_material(self, key_material: bytes) -> bytes:
        """Encrypt key material using KEK"""
        fernet = Fernet(self.kek)
        return fernet.encrypt(key_material)
    
    async def _cache_key(self, key: EncryptionKey):
        """Cache key in Redis"""
        cache_key = f"active_key:{key.key_type.value}"
        await self.redis_client.setex(
            cache_key,
            3600,  # 1 hour TTL
            key.json()
        )
    
    async def _schedule_rotations(self):
        """Schedule automatic key rotations"""
        # Check for keys needing rotation
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT key_type
                FROM key_management.encryption_keys
                WHERE status = 'active'
                AND expires_at <= NOW() + INTERVAL '7 days'
            """)
            
            for row in rows:
                key_type = KeyType(row['key_type'])
                await self.rotate_key(key_type, "Scheduled rotation - approaching expiration")
    
    async def _schedule_key_expiration(self, key_id: str, days: int = 30):
        """Schedule a key for expiration"""
        expiration_date = datetime.utcnow() + timedelta(days=days)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE key_management.encryption_keys
                SET expires_at = $1
                WHERE key_id = $2
            """, expiration_date, UUID(key_id))
    
    async def _audit_key_operation(
        self,
        key_id: str,
        operation: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Audit key operations"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO key_management.key_usage_audit (
                    key_id, operation, success, metadata
                ) VALUES ($1, $2, $3, $4)
            """, UUID(key_id), operation, success,
                json.dumps(metadata) if metadata else None)
    
    async def encrypt_data(
        self,
        data: bytes,
        key_type: KeyType = KeyType.DATA_ENCRYPTION
    ) -> Tuple[bytes, str, int]:
        """
        Encrypt data using the active key
        
        Returns:
            Tuple of (encrypted_data, key_id, key_version)
        """
        key = await self.get_active_key(key_type)
        if not key:
            raise ValueError(f"No active key for type {key_type}")
        
        # Decrypt key material
        key_material = self.decrypt_key_material(key.key_material)
        
        # Encrypt data
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(key_material),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Return encrypted data with IV and tag
        encrypted = iv + ciphertext + encryptor.tag
        
        await self._audit_key_operation(key.key_id, "encrypt", True)
        
        return encrypted, key.key_id, key.key_version
    
    async def decrypt_data(
        self,
        encrypted_data: bytes,
        key_id: Optional[str] = None,
        key_version: Optional[int] = None,
        key_type: KeyType = KeyType.DATA_ENCRYPTION
    ) -> bytes:
        """Decrypt data using specified key"""
        # Get the appropriate key
        if key_id:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM key_management.encryption_keys
                    WHERE key_id = $1
                """, UUID(key_id))
                if not row:
                    raise ValueError(f"Key {key_id} not found")
                key = EncryptionKey(
                    key_id=str(row['key_id']),
                    key_type=KeyType(row['key_type']),
                    key_version=row['key_version'],
                    algorithm=row['algorithm'],
                    key_material=row['encrypted_key_material']
                )
        elif key_version:
            key = await self.get_key_by_version(key_type, key_version)
            if not key:
                raise ValueError(f"Key version {key_version} not found")
        else:
            key = await self.get_active_key(key_type)
            if not key:
                raise ValueError(f"No active key for type {key_type}")
        
        # Decrypt key material
        key_material = self.decrypt_key_material(key.key_material)
        
        # Extract components
        iv = encrypted_data[:12]
        tag = encrypted_data[-16:]
        ciphertext = encrypted_data[12:-16]
        
        # Decrypt data
        cipher = Cipher(
            algorithms.AES(key_material),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        await self._audit_key_operation(key.key_id, "decrypt", True)
        
        return plaintext


# Export main class
__all__ = ['SecureKeyManagementSystem', 'KeyType', 'KeyStatus', 'EncryptionKey']
