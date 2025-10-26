"""
Core Audit Trail System
Simplified implementation for secure audit logging
"""

import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
import redis.asyncio as redis
import asyncpg
from pydantic import BaseModel, Field
from fastapi import Request, Response


class AuditEventType(str, Enum):
    """Core audit event types"""
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGED = "auth.password.changed"
    MFA_VERIFIED = "auth.mfa.verified"
    
    # Data operations
    DATA_READ = "data.read"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    
    # Security
    PERMISSION_CHANGED = "permission.changed"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    SECURITY_ALERT = "security.alert"
    
    # System
    CONFIG_CHANGED = "config.changed"
    ERROR = "system.error"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Core audit event model"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO
    description: str
    
    # Actor
    actor_id: Optional[str] = None
    actor_type: str = "user"
    actor_ip: Optional[str] = None
    
    # Target
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    
    # Context
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    hash: Optional[str] = None


class AuditTrail:
    """Simplified audit trail implementation"""
    
    def __init__(
        self,
        database_url: str,
        redis_url: str,
        retention_days: int = 2555  # 7 years
    ):
        self.database_url = database_url
        self.redis_url = redis_url
        self.retention_days = retention_days
        self.redis_client: Optional[redis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.event_buffer: List[AuditEvent] = []
        self.buffer_size = 100
        self.last_flush = datetime.utcnow()
    
    async def init(self):
        """Initialize connections"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        self.db_pool = await asyncpg.create_pool(self.database_url)
        await self._create_tables()
    
    async def close(self):
        """Close connections"""
        await self.flush()
        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def log(
        self,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Log an audit event"""
        # Create event
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            actor_id=actor_id,
            target_id=target_id,
            metadata=self._filter_sensitive(metadata) if metadata else None,
            **kwargs
        )
        
        # Extract request info
        if request:
            event.actor_ip = request.client.host if request.client else None
            event.request_id = request.headers.get("X-Request-ID")
            if hasattr(request.state, "tenant_id"):
                event.tenant_id = request.state.tenant_id
            if hasattr(request.state, "session_id"):
                event.session_id = request.state.session_id
        
        # Add hash for integrity
        event.hash = self._hash_event(event)
        
        # Buffer event
        self.event_buffer.append(event)
        
        # Check if flush needed
        if len(self.event_buffer) >= self.buffer_size:
            await self.flush()
        
        # Send alert for critical events
        if severity == AuditSeverity.CRITICAL:
            await self._send_alert(event)
        
        return event.event_id
    
    async def flush(self):
        """Flush buffered events to storage"""
        if not self.event_buffer:
            return
        
        events = self.event_buffer.copy()
        self.event_buffer.clear()
        
        # Write to database
        await self._write_to_db(events)
        
        # Write to Redis for real-time access
        await self._write_to_redis(events)
        
        self.last_flush = datetime.utcnow()
    
    async def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        actor_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit events"""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_date:
            params.append(start_date)
            query += f" AND timestamp >= ${len(params)}"
        
        if end_date:
            params.append(end_date)
            query += f" AND timestamp <= ${len(params)}"
        
        if event_types:
            params.append(event_types)
            query += f" AND event_type = ANY(${len(params)})"
        
        if actor_id:
            params.append(actor_id)
            query += f" AND actor_id = ${len(params)}"
        
        if tenant_id:
            params.append(tenant_id)
            query += f" AND tenant_id = ${len(params)}"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def verify_integrity(
        self,
        event_id: str
    ) -> bool:
        """Verify event integrity by hash"""
        query = "SELECT * FROM audit_events WHERE event_id = $1"
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, event_id)
            if not row:
                return False
            
            # Recreate hash and compare
            stored_hash = row['hash']
            event_data = {
                'event_id': row['event_id'],
                'timestamp': row['timestamp'].isoformat(),
                'event_type': row['event_type'],
                'description': row['description']
            }
            calculated_hash = hashlib.sha256(
                json.dumps(event_data, sort_keys=True).encode()
            ).hexdigest()
            
            return stored_hash == calculated_hash
    
    async def get_statistics(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get audit statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
            SELECT 
                COUNT(*) as total,
                event_type,
                severity,
                DATE(timestamp) as date
            FROM audit_events
            WHERE timestamp >= $1
        """
        
        params = [start_date]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)
        
        query += " GROUP BY event_type, severity, DATE(timestamp)"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        stats = {
            "total_events": sum(row['total'] for row in rows),
            "by_type": {},
            "by_severity": {},
            "by_date": {}
        }
        
        for row in rows:
            event_type = row['event_type']
            severity = row['severity']
            date = row['date'].isoformat()
            
            stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + row['total']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + row['total']
            stats['by_date'][date] = stats['by_date'].get(date, 0) + row['total']
        
        return stats
    
    # Helper methods
    
    def _filter_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive fields"""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'ssn']
        filtered = {}
        
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_fields):
                filtered[key] = "***REDACTED***"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive(value)
            else:
                filtered[key] = value
        
        return filtered
    
    def _hash_event(self, event: AuditEvent) -> str:
        """Generate event hash"""
        data = {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'description': event.description
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
    
    async def _create_tables(self):
        """Create audit tables"""
        query = """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id UUID PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                actor_id VARCHAR(100),
                actor_type VARCHAR(20),
                actor_ip INET,
                target_id VARCHAR(100),
                target_type VARCHAR(100),
                tenant_id VARCHAR(100),
                session_id VARCHAR(100),
                request_id VARCHAR(100),
                metadata JSONB,
                hash VARCHAR(64),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id);
            CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_events(tenant_id);
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(query)
    
    async def _write_to_db(self, events: List[AuditEvent]):
        """Write events to database"""
        query = """
            INSERT INTO audit_events (
                event_id, timestamp, event_type, severity, description,
                actor_id, actor_type, actor_ip, target_id, target_type,
                tenant_id, session_id, request_id, metadata, hash
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        """
        
        async with self.db_pool.acquire() as conn:
            values = [
                (
                    event.event_id, event.timestamp, event.event_type,
                    event.severity, event.description, event.actor_id,
                    event.actor_type, event.actor_ip, event.target_id,
                    event.target_type, event.tenant_id, event.session_id,
                    event.request_id, json.dumps(event.metadata) if event.metadata else None,
                    event.hash
                )
                for event in events
            ]
            await conn.executemany(query, values)
    
    async def _write_to_redis(self, events: List[AuditEvent]):
        """Write events to Redis"""
        pipeline = self.redis_client.pipeline()
        
        for event in events:
            # Store event
            pipeline.hset(
                f"audit:{event.event_id}",
                mapping={"data": event.json()}
            )
            pipeline.expire(f"audit:{event.event_id}", 604800)  # 7 days
            
            # Update indices
            if event.actor_id:
                pipeline.sadd(f"audit:actor:{event.actor_id}", event.event_id)
            if event.tenant_id:
                pipeline.sadd(f"audit:tenant:{event.tenant_id}", event.event_id)
        
        await pipeline.execute()
    
    async def _send_alert(self, event: AuditEvent):
        """Send alert for critical events"""
        alert = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "severity": event.severity,
            "description": event.description
        }
        
        await self.redis_client.lpush("audit:alerts", json.dumps(alert))
        await self.redis_client.ltrim("audit:alerts", 0, 999)


# Export classes
__all__ = [
    'AuditTrail',
    'AuditEvent',
    'AuditEventType',
    'AuditSeverity'
]
