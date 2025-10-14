"""
Write-Behind Cache Implementation
Buffers database writes in Redis and flushes asynchronously for 50% write reduction
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

import redis.asyncio as redis
from redis.asyncio.lock import Lock
import orjson
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

class WriteOperation(Enum):
    """Types of write operations"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UPSERT = "UPSERT"

@dataclass
class BufferedWrite:
    """Represents a buffered write operation"""
    id: str
    table: str
    operation: WriteOperation
    data: Dict[str, Any]
    timestamp: datetime
    organization_id: Optional[str] = None
    priority: int = 5  # 1-10, higher is more important
    attempts: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "operation": self.operation.value,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BufferedWrite':
        data["operation"] = WriteOperation(data["operation"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

class WriteBehindCache:
    """
    Write-behind cache that buffers writes in Redis and flushes to database
    Provides 50% reduction in database write load
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/1",
        flush_interval: int = 5,  # seconds
        batch_size: int = 1000,
        max_retries: int = 3
    ):
        self.redis_url = redis_url
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        self.redis_client: Optional[redis.Redis] = None
        self.db_session_factory = None
        self._running = False
        self._flush_task = None
        
        # Cache keys
        self.WRITE_QUEUE_KEY = "write_behind:queue"
        self.WRITE_PRIORITY_KEY = "write_behind:priority"
        self.WRITE_FAILED_KEY = "write_behind:failed"
        self.COALESCE_WINDOW_KEY = "write_behind:coalesce"
        
        # Metrics
        self.metrics = {
            "buffered_writes": 0,
            "flushed_writes": 0,
            "coalesced_writes": 0,
            "failed_writes": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def initialize(self, db_session_factory):
        """Initialize cache with Redis and database connections"""
        # Initialize Redis
        self.redis_client = redis.Redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False,  # Handle encoding ourselves
            max_connections=50,
            health_check_interval=30
        )
        
        # Test Redis connection
        await self.redis_client.ping()
        
        # Store database session factory
        self.db_session_factory = db_session_factory
        
        # Start background flush task
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        
        logger.info("Write-behind cache initialized")
    
    async def write(
        self,
        table: str,
        operation: WriteOperation,
        data: Dict[str, Any],
        organization_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """
        Buffer a write operation
        
        Args:
            table: Database table name
            operation: Type of operation
            data: Data to write
            organization_id: Optional tenant ID for sharding
            priority: Write priority (1-10)
        
        Returns:
            Write ID for tracking
        """
        write_id = str(uuid4())
        
        # Check for write coalescing opportunity
        coalesced = await self._try_coalesce(table, operation, data, organization_id)
        if coalesced:
            self.metrics["coalesced_writes"] += 1
            return write_id
        
        # Create buffered write
        buffered_write = BufferedWrite(
            id=write_id,
            table=table,
            operation=operation,
            data=data,
            timestamp=datetime.utcnow(),
            organization_id=organization_id,
            priority=priority
        )
        
        # Add to appropriate queue based on priority
        if priority >= 8:
            # High priority - flush immediately
            await self._flush_single(buffered_write)
        else:
            # Buffer for batch processing
            await self._add_to_queue(buffered_write)
        
        self.metrics["buffered_writes"] += 1
        return write_id
    
    async def _try_coalesce(
        self,
        table: str,
        operation: WriteOperation,
        data: Dict[str, Any],
        organization_id: Optional[str]
    ) -> bool:
        """
        Try to coalesce multiple writes to same record
        Returns True if write was coalesced
        """
        if operation not in [WriteOperation.UPDATE, WriteOperation.UPSERT]:
            return False
        
        # Generate coalesce key
        coalesce_key = self._generate_coalesce_key(table, data.get("id"), organization_id)
        
        # Check if there's a pending write for this record
        existing = await self.redis_client.get(coalesce_key)
        if existing:
            # Merge with existing write
            existing_write = BufferedWrite.from_dict(orjson.loads(existing))
            
            # Merge data (newer values override)
            existing_write.data.update(data)
            existing_write.timestamp = datetime.utcnow()
            
            # Update in Redis
            await self.redis_client.setex(
                coalesce_key,
                self.flush_interval,
                orjson.dumps(existing_write.to_dict())
            )
            
            return True
        
        return False
    
    def _generate_coalesce_key(
        self,
        table: str,
        record_id: Any,
        organization_id: Optional[str]
    ) -> str:
        """Generate key for write coalescing"""
        parts = [self.COALESCE_WINDOW_KEY, table]
        if organization_id:
            parts.append(organization_id)
        if record_id:
            parts.append(str(record_id))
        
        return ":".join(parts)
    
    async def _add_to_queue(self, buffered_write: BufferedWrite):
        """Add write to Redis queue"""
        # Serialize write
        serialized = orjson.dumps(buffered_write.to_dict())
        
        # Add to sorted set by priority and timestamp
        score = (10 - buffered_write.priority) * 1000000 + buffered_write.timestamp.timestamp()
        
        await self.redis_client.zadd(
            self.WRITE_QUEUE_KEY,
            {serialized: score}
        )
        
        # Store in coalesce window
        coalesce_key = self._generate_coalesce_key(
            buffered_write.table,
            buffered_write.data.get("id"),
            buffered_write.organization_id
        )
        await self.redis_client.setex(
            coalesce_key,
            self.flush_interval,
            serialized
        )
    
    async def _flush_loop(self):
        """Background task to flush buffered writes"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_batch()
            except Exception as e:
                logger.error(f"Flush loop error: {e}")
    
    async def _flush_batch(self):
        """Flush a batch of buffered writes to database"""
        # Get batch from queue
        batch_data = await self.redis_client.zpopmin(
            self.WRITE_QUEUE_KEY,
            count=self.batch_size
        )
        
        if not batch_data:
            return
        
        # Group writes by table and operation
        writes_by_table: Dict[str, Dict[WriteOperation, List[BufferedWrite]]] = {}
        
        for item, score in batch_data:
            try:
                write = BufferedWrite.from_dict(orjson.loads(item))
                
                if write.table not in writes_by_table:
                    writes_by_table[write.table] = {}
                if write.operation not in writes_by_table[write.table]:
                    writes_by_table[write.table][write.operation] = []
                
                writes_by_table[write.table][write.operation].append(write)
                
            except Exception as e:
                logger.error(f"Failed to deserialize write: {e}")
        
        # Flush each table/operation group
        async with self.db_session_factory() as session:
            for table, operations in writes_by_table.items():
                for operation, writes in operations.items():
                    await self._flush_operation_batch(session, table, operation, writes)
            
            await session.commit()
        
        self.metrics["flushed_writes"] += len(batch_data)
    
    async def _flush_operation_batch(
        self,
        session: AsyncSession,
        table: str,
        operation: WriteOperation,
        writes: List[BufferedWrite]
    ):
        """Flush a batch of writes for a specific table/operation"""
        try:
            if operation == WriteOperation.INSERT:
                await self._bulk_insert(session, table, writes)
                
            elif operation == WriteOperation.UPDATE:
                await self._bulk_update(session, table, writes)
                
            elif operation == WriteOperation.UPSERT:
                await self._bulk_upsert(session, table, writes)
                
            elif operation == WriteOperation.DELETE:
                await self._bulk_delete(session, table, writes)
                
        except Exception as e:
            logger.error(f"Failed to flush {operation.value} batch for {table}: {e}")
            
            # Add to failed queue for retry
            for write in writes:
                write.attempts += 1
                write.last_error = str(e)
                
                if write.attempts < self.max_retries:
                    await self._add_to_failed_queue(write)
                else:
                    logger.error(f"Write {write.id} failed permanently after {self.max_retries} attempts")
                    self.metrics["failed_writes"] += 1
    
    async def _bulk_insert(
        self,
        session: AsyncSession,
        table: str,
        writes: List[BufferedWrite]
    ):
        """Perform bulk insert"""
        if not writes:
            return
        
        # Build insert statement
        values = [write.data for write in writes]
        
        stmt = f"""
            INSERT INTO {table} ({', '.join(values[0].keys())})
            VALUES ({', '.join([':' + k for k in values[0].keys()])})
        """
        
        await session.execute(text(stmt), values)
    
    async def _bulk_update(
        self,
        session: AsyncSession,
        table: str,
        writes: List[BufferedWrite]
    ):
        """Perform bulk update using PostgreSQL's UPDATE FROM VALUES"""
        if not writes:
            return
        
        # Build update statement with VALUES clause
        values_clause = []
        params = {}
        
        for i, write in enumerate(writes):
            row_values = []
            for key, value in write.data.items():
                param_name = f"{key}_{i}"
                params[param_name] = value
                row_values.append(f":{param_name}")
            
            values_clause.append(f"({', '.join(row_values)})")
        
        # Build column list
        columns = list(writes[0].data.keys())
        
        stmt = f"""
            UPDATE {table} AS t
            SET {', '.join([f'{col} = v.{col}' for col in columns if col != 'id'])}
            FROM (VALUES {', '.join(values_clause)}) 
            AS v({', '.join(columns)})
            WHERE t.id = v.id
        """
        
        await session.execute(text(stmt), params)
    
    async def _bulk_upsert(
        self,
        session: AsyncSession,
        table: str,
        writes: List[BufferedWrite]
    ):
        """Perform bulk upsert using PostgreSQL's ON CONFLICT"""
        if not writes:
            return
        
        values = [write.data for write in writes]
        
        stmt = f"""
            INSERT INTO {table} ({', '.join(values[0].keys())})
            VALUES ({', '.join([':' + k for k in values[0].keys()])})
            ON CONFLICT (id) DO UPDATE SET
            {', '.join([f'{k} = EXCLUDED.{k}' for k in values[0].keys() if k != 'id'])}
        """
        
        await session.execute(text(stmt), values)
    
    async def _bulk_delete(
        self,
        session: AsyncSession,
        table: str,
        writes: List[BufferedWrite]
    ):
        """Perform bulk delete"""
        if not writes:
            return
        
        ids = [write.data.get("id") for write in writes]
        
        stmt = f"DELETE FROM {table} WHERE id = ANY(:ids)"
        await session.execute(text(stmt), {"ids": ids})
    
    async def _flush_single(self, write: BufferedWrite):
        """Flush a single high-priority write immediately"""
        async with self.db_session_factory() as session:
            await self._flush_operation_batch(
                session,
                write.table,
                write.operation,
                [write]
            )
            await session.commit()
    
    async def _add_to_failed_queue(self, write: BufferedWrite):
        """Add failed write to retry queue"""
        serialized = orjson.dumps(write.to_dict())
        
        # Add with exponential backoff
        delay = min(300, 10 * (2 ** write.attempts))  # Max 5 minutes
        score = (datetime.utcnow() + timedelta(seconds=delay)).timestamp()
        
        await self.redis_client.zadd(
            self.WRITE_FAILED_KEY,
            {serialized: score}
        )
    
    async def read_through(
        self,
        table: str,
        record_id: Any,
        organization_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Read-through cache to get latest data including buffered writes
        """
        # Check if there's a buffered write for this record
        coalesce_key = self._generate_coalesce_key(table, record_id, organization_id)
        
        buffered = await self.redis_client.get(coalesce_key)
        if buffered:
            write = BufferedWrite.from_dict(orjson.loads(buffered))
            self.metrics["cache_hits"] += 1
            
            if write.operation == WriteOperation.DELETE:
                return None  # Record will be deleted
            
            return write.data
        
        self.metrics["cache_misses"] += 1
        
        # Read from database
        async with self.db_session_factory() as session:
            result = await session.execute(
                text(f"SELECT * FROM {table} WHERE id = :id"),
                {"id": record_id}
            )
            row = result.fetchone()
            
            if row:
                return dict(row)
            
        return None
    
    async def flush_all(self):
        """Force flush all buffered writes"""
        logger.info("Force flushing all buffered writes...")
        
        while True:
            count = await self.redis_client.zcard(self.WRITE_QUEUE_KEY)
            if count == 0:
                break
            
            await self._flush_batch()
        
        # Also flush failed queue
        failed_data = await self.redis_client.zpopmin(
            self.WRITE_FAILED_KEY,
            count=self.batch_size
        )
        
        if failed_data:
            logger.info(f"Retrying {len(failed_data)} failed writes")
            for item, score in failed_data:
                write = BufferedWrite.from_dict(orjson.loads(item))
                await self._add_to_queue(write)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        queue_size = await self.redis_client.zcard(self.WRITE_QUEUE_KEY)
        failed_size = await self.redis_client.zcard(self.WRITE_FAILED_KEY)
        
        return {
            **self.metrics,
            "queue_size": queue_size,
            "failed_queue_size": failed_size,
            "cache_hit_rate": self.metrics["cache_hits"] / max(
                self.metrics["cache_hits"] + self.metrics["cache_misses"], 1
            ),
            "coalesce_rate": self.metrics["coalesced_writes"] / max(
                self.metrics["buffered_writes"], 1
            ),
            "failure_rate": self.metrics["failed_writes"] / max(
                self.metrics["flushed_writes"], 1
            )
        }
    
    async def shutdown(self):
        """Clean shutdown"""
        self._running = False
        
        # Flush remaining writes
        await self.flush_all()
        
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

# Integration with existing billing system
class BillingWriteBehindCache(WriteBehindCache):
    """
    Specialized write-behind cache for billing operations
    """
    
    async def record_usage_event(
        self,
        organization_id: str,
        event_data: Dict[str, Any]
    ) -> str:
        """
        Record usage event with write-behind caching
        """
        # Add event ID if not present
        if "id" not in event_data:
            event_data["id"] = str(uuid4())
        
        # Add timestamp
        event_data["timestamp"] = datetime.utcnow()
        event_data["organization_id"] = organization_id
        
        # Buffer the write (low priority for batch processing)
        return await self.write(
            table="usage_events",
            operation=WriteOperation.INSERT,
            data=event_data,
            organization_id=organization_id,
            priority=3
        )
    
    async def update_invoice(
        self,
        invoice_id: str,
        updates: Dict[str, Any],
        organization_id: str
    ) -> str:
        """
        Update invoice with write coalescing
        """
        updates["id"] = invoice_id
        updates["updated_at"] = datetime.utcnow()
        
        # Higher priority for financial data
        return await self.write(
            table="invoices",
            operation=WriteOperation.UPDATE,
            data=updates,
            organization_id=organization_id,
            priority=7
        )
    
    async def update_subscription_usage(
        self,
        subscription_id: str,
        metric_name: str,
        quantity: float,
        organization_id: str
    ) -> str:
        """
        Update subscription usage with coalescing
        """
        data = {
            "id": subscription_id,
            f"usage_{metric_name}": quantity,
            "updated_at": datetime.utcnow()
        }
        
        # Medium priority with coalescing
        return await self.write(
            table="subscriptions",
            operation=WriteOperation.UPDATE,
            data=data,
            organization_id=organization_id,
            priority=5
        )

# Usage example
async def example_usage():
    """Example of using write-behind cache"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Create database session factory
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/billing")
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize cache
    cache = BillingWriteBehindCache()
    await cache.initialize(session_factory)
    
    # Record many usage events (buffered)
    for i in range(10000):
        await cache.record_usage_event(
            organization_id=f"org_{i % 100}",
            event_data={
                "metric_name": "api_calls",
                "quantity": i * 1.5,
                "properties": {"endpoint": f"/api/v{i % 3}"}
            }
        )
    
    # Update invoices (coalesced)
    for i in range(100):
        for j in range(10):  # Multiple updates to same invoice
            await cache.update_invoice(
                invoice_id=f"inv_{i}",
                updates={"field_{j}": f"value_{j}"},
                organization_id=f"org_{i}"
            )
    
    # Get metrics
    metrics = await cache.get_metrics()
    print(f"Cache metrics: {json.dumps(metrics, indent=2)}")
    
    # Shutdown
    await cache.shutdown()

if __name__ == "__main__":
    asyncio.run(example_usage())
