"""
Database Security Integration for ValueVerse Billing System
Implements RLS, encryption, and audit trail from application layer
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from uuid import UUID
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, event
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)

class SecureDatabase:
    """
    Secure database connection with RLS, encryption, and audit trail
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize secure database connection"""
        if self._initialized:
            return
            
        # Create engine with security settings
        self.engine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=30,
            echo=False,
            connect_args={
                "server_settings": {
                    "application_name": "billing_secure",
                    "row_security": "on",
                    "statement_timeout": "30s",
                    "lock_timeout": "10s"
                },
                "ssl": "require",
                "ssl_min_protocol": "TLSv1.2"
            }
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Set up event listeners for security
        self._setup_event_listeners()
        
        self._initialized = True
        logger.info("Secure database initialized")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for security"""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set session parameters on connect"""
            with dbapi_conn.cursor() as cursor:
                # Enable RLS
                cursor.execute("SET row_security = ON")
                # Set statement timeout
                cursor.execute("SET statement_timeout = '30s'")
                # Set lock timeout
                cursor.execute("SET lock_timeout = '10s'")
        
        @event.listens_for(self.engine.sync_engine, "before_execute")
        def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
            """Log and audit queries"""
            # This is where you'd implement query logging/auditing
            pass
    
    @asynccontextmanager
    async def get_secure_session(self, tenant_id: UUID, user_id: Optional[str] = None):
        """
        Get a database session with tenant context for RLS
        
        Args:
            tenant_id: The tenant ID to set for RLS
            user_id: Optional user ID for audit trail
        """
        async with self.session_factory() as session:
            try:
                # Set tenant context for RLS
                await session.execute(
                    text("SELECT set_tenant_context(:tenant_id)"),
                    {"tenant_id": str(tenant_id)}
                )
                
                # Set session ID for audit trail
                session_id = f"{tenant_id}:{datetime.utcnow().isoformat()}"
                await session.execute(
                    text("SET LOCAL app.session_id = :session_id"),
                    {"session_id": session_id}
                )
                
                # Set user ID if provided
                if user_id:
                    await session.execute(
                        text("SET LOCAL app.current_user = :user_id"),
                        {"user_id": user_id}
                    )
                
                yield session
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                # Clear tenant context
                await session.execute(text("SET LOCAL app.current_tenant = ''"))
                await session.close()

class EncryptionManager:
    """
    Manages field-level encryption for sensitive data
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = self._load_master_key(master_key)
        self.fernet = Fernet(
            self.master_key.encode() if isinstance(self.master_key, str) else self.master_key
        )

    def _load_master_key(self, override_key: Optional[Union[str, bytes]]) -> Union[str, bytes]:
        """Load the encryption master key with fail-safe semantics."""
        key: Optional[Union[str, bytes]] = override_key or os.getenv("ENCRYPTION_MASTER_KEY")

        if not key:
            # In production a dedicated KMS should be used. Failing fast prevents
            # the application from running with an unknown transient key which
            # would make existing ciphertext irrecoverable.
            raise RuntimeError(
                "Encryption master key is not configured. Set ENCRYPTION_MASTER_KEY "
                "or provide a key via EncryptionManager(master_key=...)."
            )

        return key
    
    def encrypt(self, plain_text: str) -> bytes:
        """Encrypt sensitive data"""
        if not plain_text:
            return None
        return self.fernet.encrypt(plain_text.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        return self.fernet.decrypt(encrypted_data).decode()
    
    def encrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[f"{field}_encrypted"] = self.encrypt(str(encrypted_data[field]))
                encrypted_data[field] = None  # Clear plaintext
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        for field in fields:
            encrypted_field = f"{field}_encrypted"
            if encrypted_field in decrypted_data and decrypted_data[encrypted_field]:
                decrypted_data[field] = self.decrypt(decrypted_data[encrypted_field])
        return decrypted_data

class AuditLogger:
    """
    Handles audit logging for compliance
    """
    
    def __init__(self, db: SecureDatabase):
        self.db = db
    
    async def log_access(
        self,
        user_id: str,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data access for audit trail"""
        async with self.db.get_secure_session(tenant_id, user_id) as session:
            await session.execute(
                text("""
                    INSERT INTO security_audit_log 
                    (event_type, user_id, tenant_id, details, timestamp)
                    VALUES (:event_type, :user_id, :tenant_id, :details, NOW())
                """),
                {
                    "event_type": f"{resource_type}_{action}",
                    "user_id": user_id,
                    "tenant_id": str(tenant_id),
                    "details": details or {}
                }
            )
    
    async def log_sensitive_operation(
        self,
        user_id: str,
        tenant_id: UUID,
        operation: str,
        table_name: str,
        record_id: UUID,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None
    ):
        """Log sensitive operations for compliance"""
        # Mask sensitive data before logging
        masked_old = self._mask_sensitive_data(old_values) if old_values else None
        masked_new = self._mask_sensitive_data(new_values) if new_values else None
        
        async with self.db.get_secure_session(tenant_id, user_id) as session:
            await session.execute(
                text("""
                    INSERT INTO audit_trail 
                    (table_name, record_id, operation, user_id, tenant_id,
                     old_values, new_values, occurred_at)
                    VALUES (:table_name, :record_id, :operation, :user_id, :tenant_id,
                            :old_values, :new_values, NOW())
                """),
                {
                    "table_name": table_name,
                    "record_id": str(record_id),
                    "operation": operation,
                    "user_id": user_id,
                    "tenant_id": str(tenant_id),
                    "old_values": masked_old,
                    "new_values": masked_new
                }
            )
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in data"""
        if not data:
            return data
            
        masked = data.copy()
        sensitive_fields = [
            'card_number', 'cvv', 'account_number', 
            'routing_number', 'tax_id', 'ssn'
        ]
        
        for field in sensitive_fields:
            if field in masked:
                if masked[field]:
                    # Keep last 4 characters
                    masked[field] = '*' * (len(str(masked[field])) - 4) + str(masked[field])[-4:]
        
        return masked

class SecurityMonitor:
    """
    Monitors for security violations and suspicious activity
    """
    
    def __init__(self, db: SecureDatabase):
        self.db = db
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback):
        """Add callback for security alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_rls_violations(self, minutes: int = 10) -> List[Dict]:
        """Check for RLS violation attempts"""
        async with self.db.session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM vw_rls_violations
                    WHERE timestamp > NOW() - INTERVAL ':minutes minutes'
                    ORDER BY timestamp DESC
                """),
                {"minutes": minutes}
            )
            
            violations = result.fetchall()
            
            if violations:
                for callback in self.alert_callbacks:
                    await callback("RLS_VIOLATION", violations)
            
            return violations
    
    async def check_suspicious_activity(self) -> List[Dict]:
        """Check for suspicious database activity"""
        async with self.db.session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM detect_suspicious_activity()")
            )
            
            activities = result.fetchall()
            
            for activity in activities:
                if activity['severity'] == 'CRITICAL':
                    for callback in self.alert_callbacks:
                        await callback("SUSPICIOUS_ACTIVITY", activity)
            
            return activities
    
    async def verify_audit_integrity(self, days: int = 7) -> bool:
        """Verify audit trail integrity"""
        async with self.db.session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT * FROM verify_audit_trail_integrity(
                        CURRENT_DATE - INTERVAL ':days days',
                        CURRENT_DATE
                    )
                """),
                {"days": days}
            )
            
            integrity = result.fetchone()
            
            if not integrity['is_valid']:
                logger.error(f"Audit trail integrity check failed: {integrity['details']}")
                for callback in self.alert_callbacks:
                    await callback("AUDIT_INTEGRITY_FAILURE", integrity)
            
            return integrity['is_valid']

# Usage example
async def example_usage():
    """Example of using the secure database features"""
    
    # Initialize secure database
    db = SecureDatabase("postgresql+asyncpg://user:pass@localhost/billing")
    await db.initialize()
    
    # Initialize encryption
    encryption = EncryptionManager()
    
    # Initialize audit logger
    audit = AuditLogger(db)
    
    # Initialize security monitor
    monitor = SecurityMonitor(db)
    
    # Add alert callback
    async def security_alert(alert_type: str, details: Any):
        logger.critical(f"SECURITY ALERT: {alert_type} - {details}")
        # Send to monitoring system, email, etc.
    
    monitor.add_alert_callback(security_alert)
    
    # Example: Secure database operation with RLS
    tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    user_id = "user123"
    
    async with db.get_secure_session(tenant_id, user_id) as session:
        # This query will automatically be filtered by tenant_id due to RLS
        result = await session.execute(
            text("SELECT * FROM organizations WHERE id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
        
        org = result.fetchone()
        
        # Log the access
        await audit.log_access(
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="organization",
            resource_id=tenant_id,
            action="read",
            details={"purpose": "billing_overview"}
        )
    
    # Example: Encrypt sensitive data before storage
    payment_data = {
        "card_number": "4111111111111111",
        "cvv": "123",
        "exp_month": 12,
        "exp_year": 2025
    }
    
    encrypted_payment = encryption.encrypt_dict(
        payment_data,
        fields=["card_number", "cvv"]
    )
    
    # Store encrypted_payment in database
    # ...
    
    # Example: Monitor for security issues
    await monitor.check_rls_violations()
    await monitor.check_suspicious_activity()
    await monitor.verify_audit_integrity()
    
    logger.info("Security checks completed")

if __name__ == "__main__":
    asyncio.run(example_usage())
