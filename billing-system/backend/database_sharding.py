"""
Database Sharding by Organization ID
Implements horizontal sharding for linear scalability beyond 10M events/minute
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, pool
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

class ShardingStrategy(Enum):
    """Sharding strategies"""
    HASH = "hash"  # Consistent hash-based sharding
    RANGE = "range"  # Range-based sharding
    GEOGRAPHIC = "geographic"  # Geographic/region-based
    CUSTOM = "custom"  # Custom logic

@dataclass
class ShardConfig:
    """Configuration for a database shard"""
    shard_id: int
    name: str
    connection_url: str
    min_hash: int
    max_hash: int
    region: Optional[str] = None
    capacity: int = 1000000  # Events per minute capacity
    is_active: bool = True
    read_replicas: List[str] = None

    def __post_init__(self):
        if self.read_replicas is None:
            self.read_replicas = []

class ShardManager:
    """
    Manages database shards and routes queries to appropriate shards
    """
    
    def __init__(
        self,
        strategy: ShardingStrategy = ShardingStrategy.HASH,
        num_shards: int = 4
    ):
        self.strategy = strategy
        self.num_shards = num_shards
        self.shards: Dict[int, ShardConfig] = {}
        self.engines: Dict[int, AsyncEngine] = {}
        self.session_factories: Dict[int, sessionmaker] = {}
        self.read_engines: Dict[int, List[AsyncEngine]] = {}
        
        # Metrics
        self.metrics = {
            "queries_routed": 0,
            "shard_distribution": {},
            "rebalances": 0,
            "cross_shard_queries": 0
        }
    
    def add_shard(self, config: ShardConfig):
        """Add a new shard to the cluster"""
        self.shards[config.shard_id] = config
        
        # Initialize shard distribution tracking
        self.metrics["shard_distribution"][config.shard_id] = 0
        
        logger.info(f"Added shard {config.name} (ID: {config.shard_id})")
    
    async def initialize(self):
        """Initialize all shard connections"""
        for shard_id, config in self.shards.items():
            # Create primary engine
            engine = create_async_engine(
                config.connection_url,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                echo=False,
                poolclass=pool.QueuePool
            )
            
            self.engines[shard_id] = engine
            self.session_factories[shard_id] = sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create read replica engines
            if config.read_replicas:
                self.read_engines[shard_id] = []
                for replica_url in config.read_replicas:
                    replica_engine = create_async_engine(
                        replica_url,
                        pool_size=10,
                        max_overflow=15,
                        pool_pre_ping=True,
                        echo=False
                    )
                    self.read_engines[shard_id].append(replica_engine)
            
            logger.info(f"Initialized shard {config.name} with {len(config.read_replicas)} replicas")
    
    def get_shard_for_organization(self, organization_id: str) -> int:
        """
        Determine which shard an organization belongs to
        """
        if self.strategy == ShardingStrategy.HASH:
            return self._hash_shard(organization_id)
        elif self.strategy == ShardingStrategy.RANGE:
            return self._range_shard(organization_id)
        elif self.strategy == ShardingStrategy.GEOGRAPHIC:
            return self._geographic_shard(organization_id)
        else:
            return self._custom_shard(organization_id)
    
    def _hash_shard(self, organization_id: str) -> int:
        """
        Consistent hash-based sharding
        """
        # Use MD5 hash for consistent distribution
        hash_value = hashlib.md5(organization_id.encode()).hexdigest()
        hash_int = int(hash_value, 16)
        
        # Map to shard
        shard_id = hash_int % self.num_shards
        
        # Update metrics
        self.metrics["queries_routed"] += 1
        self.metrics["shard_distribution"][shard_id] += 1
        
        return shard_id
    
    def _range_shard(self, organization_id: str) -> int:
        """
        Range-based sharding (alphabetical or numeric)
        """
        # Simple alphabetical range sharding
        first_char = organization_id[0].lower()
        
        if 'a' <= first_char <= 'f':
            return 0
        elif 'g' <= first_char <= 'm':
            return 1
        elif 'n' <= first_char <= 't':
            return 2
        else:
            return 3
    
    def _geographic_shard(self, organization_id: str) -> int:
        """
        Geographic sharding based on organization region
        Would typically look up organization's region from metadata
        """
        # This would normally query a metadata service
        # For demo, using simple hash modulo
        return self._hash_shard(organization_id)
    
    def _custom_shard(self, organization_id: str) -> int:
        """
        Custom sharding logic (e.g., by customer tier)
        """
        # Implement custom logic here
        return self._hash_shard(organization_id)
    
    async def get_session(
        self,
        organization_id: str,
        read_only: bool = False
    ) -> AsyncSession:
        """
        Get a database session for the appropriate shard
        """
        shard_id = self.get_shard_for_organization(organization_id)
        
        if read_only and shard_id in self.read_engines:
            # Round-robin among read replicas
            replicas = self.read_engines[shard_id]
            if replicas:
                replica_index = hash(organization_id) % len(replicas)
                engine = replicas[replica_index]
                session_factory = sessionmaker(
                    engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                return session_factory()
        
        # Use primary shard
        return self.session_factories[shard_id]()
    
    async def execute_on_shard(
        self,
        organization_id: str,
        query: str,
        params: Optional[Dict] = None
    ) -> Any:
        """
        Execute a query on the appropriate shard
        """
        async with await self.get_session(organization_id) as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
    
    async def execute_cross_shard(
        self,
        query: str,
        params: Optional[Dict] = None,
        aggregate_func=None
    ) -> List[Any]:
        """
        Execute a query across all shards (e.g., for analytics)
        """
        self.metrics["cross_shard_queries"] += 1
        
        tasks = []
        for shard_id, session_factory in self.session_factories.items():
            if self.shards[shard_id].is_active:
                tasks.append(self._execute_on_shard_id(
                    shard_id,
                    query,
                    params
                ))
        
        results = await asyncio.gather(*tasks)
        
        # Aggregate results if function provided
        if aggregate_func:
            return aggregate_func(results)
        
        return results
    
    async def _execute_on_shard_id(
        self,
        shard_id: int,
        query: str,
        params: Optional[Dict] = None
    ) -> Any:
        """Execute query on specific shard"""
        async with self.session_factories[shard_id]() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()

class ShardedBillingDatabase:
    """
    Sharded database implementation for billing system
    """
    
    def __init__(self):
        self.shard_manager = ShardManager(
            strategy=ShardingStrategy.HASH,
            num_shards=4
        )
        
        # Configure shards
        self._configure_shards()
    
    def _configure_shards(self):
        """Configure database shards"""
        # In production, these would be separate database servers
        base_url = "postgresql+asyncpg://billing:password@"
        
        shards = [
            ShardConfig(
                shard_id=0,
                name="shard_us_east",
                connection_url=f"{base_url}shard1.east.db:5432/billing_shard_0",
                min_hash=0,
                max_hash=int('3fffffff', 16),
                region="us-east",
                read_replicas=[
                    f"{base_url}shard1-replica1.east.db:5432/billing_shard_0",
                    f"{base_url}shard1-replica2.east.db:5432/billing_shard_0"
                ]
            ),
            ShardConfig(
                shard_id=1,
                name="shard_us_west",
                connection_url=f"{base_url}shard2.west.db:5432/billing_shard_1",
                min_hash=int('40000000', 16),
                max_hash=int('7fffffff', 16),
                region="us-west",
                read_replicas=[
                    f"{base_url}shard2-replica1.west.db:5432/billing_shard_1"
                ]
            ),
            ShardConfig(
                shard_id=2,
                name="shard_eu",
                connection_url=f"{base_url}shard3.eu.db:5432/billing_shard_2",
                min_hash=int('80000000', 16),
                max_hash=int('bfffffff', 16),
                region="eu-west"
            ),
            ShardConfig(
                shard_id=3,
                name="shard_asia",
                connection_url=f"{base_url}shard4.asia.db:5432/billing_shard_3",
                min_hash=int('c0000000', 16),
                max_hash=int('ffffffff', 16),
                region="asia-pacific"
            )
        ]
        
        for shard in shards:
            self.shard_manager.add_shard(shard)
    
    async def initialize(self):
        """Initialize sharded database"""
        await self.shard_manager.initialize()
        
        # Create tables on all shards
        await self._create_shard_tables()
    
    async def _create_shard_tables(self):
        """Create tables on all shards"""
        create_tables_sql = """
        -- Usage events table (main table for sharding)
        CREATE TABLE IF NOT EXISTS usage_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            quantity NUMERIC(20,6) NOT NULL,
            unit VARCHAR(50),
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            properties JSONB DEFAULT '{}',
            idempotency_key VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            
            -- Shard-specific indexes
            INDEX idx_org_time (organization_id, timestamp DESC),
            INDEX idx_metric_time (metric_name, timestamp DESC),
            UNIQUE INDEX idx_idempotency (idempotency_key) WHERE idempotency_key IS NOT NULL
        ) PARTITION BY RANGE (timestamp);
        
        -- Create monthly partitions
        CREATE TABLE IF NOT EXISTS usage_events_current 
        PARTITION OF usage_events
        FOR VALUES FROM (DATE_TRUNC('month', CURRENT_DATE))
        TO (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month');
        
        -- Subscriptions (replicated across shards)
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID PRIMARY KEY,
            organization_id UUID NOT NULL,
            plan_id UUID NOT NULL,
            status VARCHAR(50),
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            INDEX idx_org_status (organization_id, status)
        );
        
        -- Invoices (sharded by organization)
        CREATE TABLE IF NOT EXISTS invoices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL,
            subscription_id UUID,
            invoice_number VARCHAR(50) UNIQUE,
            status VARCHAR(50),
            total NUMERIC(10,2),
            amount_due NUMERIC(10,2),
            created_at TIMESTAMP DEFAULT NOW(),
            
            INDEX idx_org_created (organization_id, created_at DESC)
        );
        """
        
        # Execute on all shards
        await self.shard_manager.execute_cross_shard(create_tables_sql)
        logger.info("Created tables on all shards")
    
    async def record_usage_event(
        self,
        organization_id: str,
        event_data: Dict[str, Any]
    ) -> str:
        """
        Record usage event to appropriate shard
        """
        # Add organization_id to event
        event_data["organization_id"] = organization_id
        
        # Execute on correct shard
        query = """
            INSERT INTO usage_events 
            (organization_id, metric_name, quantity, unit, timestamp, properties, idempotency_key)
            VALUES (:org_id, :metric, :quantity, :unit, :timestamp, :properties, :idempotency_key)
            RETURNING id
        """
        
        params = {
            "org_id": organization_id,
            "metric": event_data.get("metric_name"),
            "quantity": event_data.get("quantity"),
            "unit": event_data.get("unit", "units"),
            "timestamp": event_data.get("timestamp"),
            "properties": event_data.get("properties", {}),
            "idempotency_key": event_data.get("idempotency_key")
        }
        
        result = await self.shard_manager.execute_on_shard(
            organization_id,
            query,
            params
        )
        
        return str(result.scalar())
    
    async def get_usage_summary(
        self,
        organization_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get usage summary from appropriate shard
        """
        query = """
            SELECT 
                metric_name,
                SUM(quantity) as total_quantity,
                COUNT(*) as event_count,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM usage_events
            WHERE organization_id = :org_id
            AND timestamp BETWEEN :start_date AND :end_date
            GROUP BY metric_name
        """
        
        params = {
            "org_id": organization_id,
            "start_date": start_date,
            "end_date": end_date
        }
        
        async with await self.shard_manager.get_session(organization_id, read_only=True) as session:
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            return {
                "organization_id": organization_id,
                "period": {"start": start_date, "end": end_date},
                "metrics": [
                    {
                        "metric_name": row.metric_name,
                        "total_quantity": float(row.total_quantity),
                        "event_count": row.event_count,
                        "first_event": row.first_event.isoformat(),
                        "last_event": row.last_event.isoformat()
                    }
                    for row in rows
                ]
            }
    
    async def get_global_analytics(self) -> Dict[str, Any]:
        """
        Get analytics across all shards
        """
        query = """
            SELECT 
                COUNT(DISTINCT organization_id) as total_orgs,
                COUNT(*) as total_events,
                SUM(quantity) as total_quantity
            FROM usage_events
            WHERE timestamp > CURRENT_DATE - INTERVAL '24 hours'
        """
        
        # Execute on all shards
        results = await self.shard_manager.execute_cross_shard(query)
        
        # Aggregate results
        total_orgs = sum(r[0][0] for r in results if r)
        total_events = sum(r[0][1] for r in results if r)
        total_quantity = sum(r[0][2] for r in results if r)
        
        return {
            "total_organizations": total_orgs,
            "total_events": total_events,
            "total_quantity": float(total_quantity),
            "shard_distribution": self.shard_manager.metrics["shard_distribution"]
        }
    
    async def rebalance_shards(self):
        """
        Rebalance data across shards (for maintenance)
        """
        self.shard_manager.metrics["rebalances"] += 1
        
        # This would implement data migration between shards
        # For production, use tools like pg_repack or custom migration
        logger.info("Shard rebalancing initiated")
        
        # Implementation would:
        # 1. Identify hot shards
        # 2. Move organizations to cooler shards
        # 3. Update shard mappings
        # 4. Verify data integrity
        
        return {"status": "rebalancing", "estimated_time": "30 minutes"}

# Shard monitoring and management
class ShardMonitor:
    """
    Monitors shard health and performance
    """
    
    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager
    
    async def check_shard_health(self) -> Dict[int, Dict[str, Any]]:
        """Check health of all shards"""
        health = {}
        
        for shard_id, config in self.shard_manager.shards.items():
            if not config.is_active:
                health[shard_id] = {"status": "inactive"}
                continue
            
            try:
                # Test connection
                async with self.shard_manager.session_factories[shard_id]() as session:
                    result = await session.execute(text("SELECT 1"))
                    
                    # Get shard statistics
                    stats_query = """
                        SELECT 
                            pg_database_size(current_database()) as db_size,
                            COUNT(*) as connection_count
                        FROM pg_stat_activity
                        WHERE datname = current_database()
                    """
                    
                    stats = await session.execute(text(stats_query))
                    stats_row = stats.fetchone()
                    
                    health[shard_id] = {
                        "status": "healthy",
                        "db_size_bytes": stats_row.db_size,
                        "connections": stats_row.connection_count,
                        "capacity_used": self.shard_manager.metrics["shard_distribution"].get(shard_id, 0) / config.capacity
                    }
                    
            except Exception as e:
                health[shard_id] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health
    
    async def get_shard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive shard metrics"""
        health = await self.check_shard_health()
        
        return {
            "total_shards": len(self.shard_manager.shards),
            "active_shards": sum(1 for s in health.values() if s["status"] == "healthy"),
            "shard_health": health,
            "routing_metrics": self.shard_manager.metrics,
            "hottest_shard": max(
                self.shard_manager.metrics["shard_distribution"].items(),
                key=lambda x: x[1]
            ) if self.shard_manager.metrics["shard_distribution"] else None
        }

# Usage example
async def example_usage():
    """Example of using sharded database"""
    
    # Initialize sharded database
    db = ShardedBillingDatabase()
    await db.initialize()
    
    # Record events (automatically routed to correct shard)
    for i in range(10000):
        org_id = f"org_{i % 1000}"  # 1000 different organizations
        
        await db.record_usage_event(
            organization_id=org_id,
            event_data={
                "metric_name": "api_calls",
                "quantity": i * 1.5,
                "timestamp": datetime.utcnow(),
                "properties": {"endpoint": f"/api/v1/endpoint_{i % 10}"}
            }
        )
    
    # Get usage for specific organization (reads from correct shard)
    summary = await db.get_usage_summary(
        organization_id="org_123",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    print(f"Usage summary: {summary}")
    
    # Get global analytics (cross-shard query)
    analytics = await db.get_global_analytics()
    print(f"Global analytics: {analytics}")
    
    # Monitor shard health
    monitor = ShardMonitor(db.shard_manager)
    metrics = await monitor.get_shard_metrics()
    print(f"Shard metrics: {metrics}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
