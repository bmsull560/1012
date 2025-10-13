"""
Performance optimizations for billing service
Target: 1M events/minute with <100ms p95 response time
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import logging
from collections import defaultdict
from contextlib import asynccontextmanager

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.dialects.postgresql import insert as pg_insert
import aiocache
from aiocache import Cache
from aiocache.serializers import JsonSerializer

logger = logging.getLogger(__name__)

class ConnectionPoolManager:
    """
    Optimized database connection pool management
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize connection pool with optimal settings"""
        self.engine = create_async_engine(
            self.database_url,
            # Connection pool settings for high concurrency
            poolclass=QueuePool,
            pool_size=20,           # Base connection pool size
            max_overflow=30,        # Additional connections when needed
            pool_timeout=30,        # Timeout for getting connection
            pool_recycle=1800,      # Recycle connections after 30 min
            pool_pre_ping=True,     # Test connections before using
            
            # Engine settings
            echo=False,             # Disable SQL logging for performance
            future=True,
            
            # Statement cache for prepared statements
            connect_args={
                "server_settings": {
                    "application_name": "billing_service",
                    "jit": "off"  # Disable JIT for consistent performance
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 1000,
                "prepared_statement_name_func": lambda stmt: f"stmt_{hash(stmt)}"
            }
        )
        
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Prevent lazy loading
            autoflush=False,        # Control flushing manually
            autocommit=False
        )
        
        logger.info("Connection pool initialized")
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with connection pooling"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

class BatchProcessor:
    """
    Batch processing for high-volume operations
    """
    
    def __init__(self, batch_size: int = 1000, flush_interval: float = 0.1):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batches = defaultdict(list)
        self.locks = defaultdict(asyncio.Lock)
        self.flush_tasks = {}
        
    async def add_to_batch(self, batch_type: str, item: Any):
        """Add item to batch for processing"""
        async with self.locks[batch_type]:
            self.batches[batch_type].append(item)
            
            # Process if batch is full
            if len(self.batches[batch_type]) >= self.batch_size:
                await self._flush_batch(batch_type)
            # Schedule flush if not already scheduled
            elif batch_type not in self.flush_tasks:
                self.flush_tasks[batch_type] = asyncio.create_task(
                    self._schedule_flush(batch_type)
                )
    
    async def _schedule_flush(self, batch_type: str):
        """Schedule batch flush after interval"""
        await asyncio.sleep(self.flush_interval)
        async with self.locks[batch_type]:
            await self._flush_batch(batch_type)
            del self.flush_tasks[batch_type]
    
    async def _flush_batch(self, batch_type: str):
        """Flush batch to database"""
        if not self.batches[batch_type]:
            return
            
        batch = self.batches[batch_type]
        self.batches[batch_type] = []
        
        # Process batch based on type
        if batch_type == "usage_events":
            await self._bulk_insert_usage_events(batch)
        # Add more batch types as needed
    
    async def _bulk_insert_usage_events(self, events: List[Dict]):
        """Bulk insert usage events using PostgreSQL COPY"""
        from backend.models import UsageEvent
        
        # Use COPY for maximum performance
        async with connection_pool.get_session() as session:
            # Build bulk insert statement with ON CONFLICT
            stmt = pg_insert(UsageEvent).values(events)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['idempotency_key']
            )
            
            await session.execute(stmt)
            logger.info(f"Bulk inserted {len(events)} usage events")

class OptimizedBillingOperations:
    """
    Optimized billing operations for high performance
    """
    
    def __init__(self, cache_manager, batch_processor):
        self.cache = cache_manager
        self.batch_processor = batch_processor
        
    async def record_usage_event_optimized(
        self,
        organization_id: UUID,
        event_data: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[Dict]:
        """
        Optimized usage event recording with batching and caching
        """
        start_time = time.time()
        
        # Quick idempotency check in cache
        idempotency_key = event_data.get("idempotency_key")
        if idempotency_key:
            cache_key = f"idempotency:{idempotency_key}"
            if await self.cache.get_multi_tier(cache_key):
                logger.debug(f"Duplicate event skipped: {idempotency_key}")
                return None
            
            # Set in cache with 24h TTL
            await self.cache.set_multi_tier(cache_key, True, ttl=86400)
        
        # Prepare event for batch processing
        event = {
            "id": str(UUID()),
            "organization_id": str(organization_id),
            "metric_name": event_data["metric_name"],
            "quantity": event_data["quantity"],
            "unit": event_data.get("unit", "units"),
            "timestamp": event_data.get("timestamp") or datetime.utcnow(),
            "properties": event_data.get("properties", {}),
            "idempotency_key": idempotency_key
        }
        
        # Add to batch
        await self.batch_processor.add_to_batch("usage_events", event)
        
        # Async check usage limits (non-blocking)
        asyncio.create_task(
            self._check_usage_limits_async(
                organization_id, 
                event_data["metric_name"],
                event_data["quantity"]
            )
        )
        
        # Track performance
        duration = time.time() - start_time
        if duration > 0.1:
            logger.warning(f"Slow usage event recording: {duration:.3f}s")
        
        return event
    
    async def get_usage_summary_optimized(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metric_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimized usage summary with caching and materialized views
        """
        # Generate cache key
        cache_key = f"usage_summary:{organization_id}:{start_date.date()}:{end_date.date()}"
        if metric_name:
            cache_key += f":{metric_name}"
        
        # Check cache
        cached = await self.cache.get_multi_tier(cache_key)
        if cached:
            return cached
        
        # Use continuous aggregate for recent data
        if (datetime.utcnow() - end_date).days < 7:
            result = await self._query_continuous_aggregate(
                organization_id, start_date, end_date, metric_name
            )
        else:
            result = await self._query_usage_events(
                organization_id, start_date, end_date, metric_name
            )
        
        # Cache result
        await self.cache.set_multi_tier(
            cache_key, result, ttl=300, cache_type="usage_summary"
        )
        
        return result
    
    async def _query_continuous_aggregate(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metric_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query from continuous aggregate for better performance"""
        async with connection_pool.get_session() as session:
            query = """
                SELECT 
                    metric_name,
                    SUM(total_quantity) as total_quantity,
                    SUM(event_count) as event_count
                FROM usage_events_hourly
                WHERE organization_id = :org_id
                AND hour >= :start_date
                AND hour < :end_date
            """
            
            params = {
                "org_id": str(organization_id),
                "start_date": start_date,
                "end_date": end_date
            }
            
            if metric_name:
                query += " AND metric_name = :metric_name"
                params["metric_name"] = metric_name
            
            query += " GROUP BY metric_name"
            
            result = await session.execute(query, params)
            
            return {
                "metrics": [
                    {
                        "metric_name": row.metric_name,
                        "total_quantity": float(row.total_quantity),
                        "event_count": row.event_count
                    }
                    for row in result
                ]
            }
    
    async def _check_usage_limits_async(
        self,
        organization_id: UUID,
        metric_name: str,
        quantity: Decimal
    ):
        """Async usage limit checking (non-blocking)"""
        try:
            # Check cached limits first
            cache_key = f"usage_limits:{organization_id}:{metric_name}"
            limit = await self.cache.get_multi_tier(cache_key)
            
            if limit and quantity > limit["threshold"]:
                # Trigger alert (non-blocking)
                logger.warning(
                    f"Usage limit approaching for {organization_id}: "
                    f"{metric_name} = {quantity}/{limit['max']}"
                )
                # Could publish to event bus here
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")

# Performance monitoring decorator
def track_performance(operation_name: str):
    """Decorator to track operation performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 0.1:  # 100ms threshold
                    logger.warning(
                        f"Slow operation {operation_name}: {duration:.3f}s"
                    )
                
                # Update metrics
                # performance_metrics.record(operation_name, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation_name} failed after {duration:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator

# Global instances
connection_pool = ConnectionPoolManager(
    "postgresql+asyncpg://billing:password@localhost/billing_db"
)
batch_processor = BatchProcessor(batch_size=1000, flush_interval=0.1)

# Initialize on startup
async def initialize_performance_optimizations():
    """Initialize all performance optimizations"""
    await connection_pool.initialize()
    await cache_manager.initialize()
    logger.info("Performance optimizations initialized")
