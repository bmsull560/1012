"""
Immutable Hash-Chained Audit Trail System (Complete)
Implements blockchain-style audit logging for compliance and non-repudiation
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import asyncpg
from pydantic import BaseModel, Field
from enum import Enum


class ImmutableAuditTrail:
    """
    Immutable Hash-Chained Audit Trail
    Implements blockchain-style logging for compliance
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.db_pool: Optional[asyncpg.Pool] = None
        self.last_hash: Optional[str] = None
    
    async def init(self):
        """Initialize database and get last hash"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10
        )
        await self._create_schema()
        self.last_hash = await self._get_last_hash()
    
    async def _create_schema(self):
        """Create immutable audit schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE SCHEMA IF NOT EXISTS audit_immutable;
                
                CREATE TABLE IF NOT EXISTS audit_immutable.audit_trail (
                    event_id UUID PRIMARY KEY,
                    block_height BIGSERIAL UNIQUE NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    actor_id VARCHAR(100),
                    target_id VARCHAR(100),
                    action VARCHAR(100) NOT NULL,
                    result VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    metadata JSONB,
                    event_hash VARCHAR(64) NOT NULL UNIQUE,
                    previous_hash VARCHAR(64),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                -- Prevent updates and deletes
                CREATE OR REPLACE FUNCTION audit_immutable.prevent_modification()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'Audit records are immutable';
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS no_update ON audit_immutable.audit_trail;
                CREATE TRIGGER no_update BEFORE UPDATE ON audit_immutable.audit_trail
                FOR EACH ROW EXECUTE FUNCTION audit_immutable.prevent_modification();
                
                DROP TRIGGER IF EXISTS no_delete ON audit_immutable.audit_trail;
                CREATE TRIGGER no_delete BEFORE DELETE ON audit_immutable.audit_trail
                FOR EACH ROW EXECUTE FUNCTION audit_immutable.prevent_modification();
            """)
    
    async def log_event(
        self,
        event_type: str,
        action: str,
        description: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        result: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an immutable audit event
        
        Returns:
            Event ID of the logged event
        """
        event_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        # Create canonical data for hashing
        canonical_data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "target_id": target_id,
            "action": action,
            "result": result,
            "description": description,
            "previous_hash": self.last_hash or "GENESIS"
        }
        
        # Calculate event hash
        event_hash = hashlib.sha256(
            json.dumps(canonical_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_immutable.audit_trail (
                    event_id, timestamp, event_type, actor_id,
                    target_id, action, result, description,
                    metadata, event_hash, previous_hash
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, UUID(event_id), timestamp, event_type, actor_id,
                target_id, action, result, description,
                json.dumps(metadata) if metadata else None,
                event_hash, self.last_hash)
        
        # Update last hash for next event
        self.last_hash = event_hash
        
        return event_id
    
    async def verify_integrity(
        self,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain
        
        Returns:
            Verification results including any broken links
        """
        async with self.db_pool.acquire() as conn:
            # Get events in order
            query = """
                SELECT event_id, event_hash, previous_hash, 
                       timestamp, event_type, actor_id, target_id,
                       action, result, description, block_height
                FROM audit_immutable.audit_trail
            """
            params = []
            
            if start_block is not None:
                query += " WHERE block_height >= $1"
                params.append(start_block)
                if end_block is not None:
                    query += " AND block_height <= $2"
                    params.append(end_block)
            elif end_block is not None:
                query += " WHERE block_height <= $1"
                params.append(end_block)
            
            query += " ORDER BY block_height ASC"
            
            rows = await conn.fetch(query, *params)
        
        # Verify chain integrity
        valid_count = 0
        invalid_blocks = []
        expected_previous = "GENESIS" if start_block == 1 or not rows else None
        
        for i, row in enumerate(rows):
            # Check hash chain
            if expected_previous and row['previous_hash'] != expected_previous:
                invalid_blocks.append({
                    "block": row['block_height'],
                    "error": "broken_chain",
                    "expected": expected_previous,
                    "actual": row['previous_hash']
                })
            else:
                valid_count += 1
            
            # Recalculate hash to verify integrity
            canonical_data = {
                "event_id": str(row['event_id']),
                "timestamp": row['timestamp'].isoformat(),
                "event_type": row['event_type'],
                "actor_id": row['actor_id'],
                "target_id": row['target_id'],
                "action": row['action'],
                "result": row['result'],
                "description": row['description'],
                "previous_hash": row['previous_hash'] or "GENESIS"
            }
            
            calculated_hash = hashlib.sha256(
                json.dumps(canonical_data, sort_keys=True).encode()
            ).hexdigest()
            
            if calculated_hash != row['event_hash']:
                invalid_blocks.append({
                    "block": row['block_height'],
                    "error": "invalid_hash",
                    "expected": calculated_hash,
                    "actual": row['event_hash']
                })
            
            expected_previous = row['event_hash']
        
        return {
            "verified": len(invalid_blocks) == 0,
            "total_blocks": len(rows),
            "valid_blocks": valid_count,
            "invalid_blocks": invalid_blocks,
            "verification_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_last_hash(self) -> Optional[str]:
        """Get the hash of the last event in the chain"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT event_hash FROM audit_immutable.audit_trail
                ORDER BY block_height DESC LIMIT 1
            """)
            return result
    
    async def query_events(
        self,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit events with filters"""
        query = "SELECT * FROM audit_immutable.audit_trail WHERE 1=1"
        params = []
        
        if event_type:
            params.append(event_type)
            query += f" AND event_type = ${len(params)}"
        
        if actor_id:
            params.append(actor_id)
            query += f" AND actor_id = ${len(params)}"
        
        if target_id:
            params.append(target_id)
            query += f" AND target_id = ${len(params)}"
        
        if start_date:
            params.append(start_date)
            query += f" AND timestamp >= ${len(params)}"
        
        if end_date:
            params.append(end_date)
            query += f" AND timestamp <= ${len(params)}"
        
        query += f" ORDER BY block_height DESC LIMIT {limit}"
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]


# Export
__all__ = ['ImmutableAuditTrail']
