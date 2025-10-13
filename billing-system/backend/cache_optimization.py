"""
Enhanced caching strategies for high-performance billing operations
Target: <100ms p95 response time with 1M events/minute
"""

import asyncio
import hashlib
import json
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
from functools import wraps
import pickle
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
import orjson
import logging

logger = logging.getLogger(__name__)

class OptimizedCacheManager:
    """
    High-performance cache manager with multi-tier caching strategy
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.local_cache = {}  # L1 cache (in-memory)
        self.redis_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        
        # Cache configuration
        self.cache_ttls = {
            "usage_summary": 300,      # 5 minutes
            "invoice": 3600,          # 1 hour
            "subscription": 600,      # 10 minutes
            "pricing_rules": 1800,    # 30 minutes
            "organization": 900,      # 15 minutes
            "payment_method": 1200,   # 20 minutes
        }
        
        # Local cache size limits
        self.max_local_cache_size = 10000
        self.local_cache_ttl = 60  # 1 minute for L1 cache
        
    async def initialize(self):
        """Initialize Redis connection pool for high throughput"""
        if self._initialized:
            return
            
        try:
            # Create connection pool for better performance
            self.redis_pool = redis.ConnectionPool(
                max_connections=50,
                max_connections_per_db=True,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                decode_responses=False,  # Handle encoding ourselves
            ).from_url(self.redis_url)
            
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            await self.redis_client.ping()
            
            self._initialized = True
            logger.info("Optimized cache manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            self._initialized = False
    
    async def get_multi_tier(self, key: str) -> Optional[Any]:
        """
        Multi-tier cache get: L1 (local) -> L2 (Redis)
        """
        # Check L1 cache first
        if key in self.local_cache:
            entry = self.local_cache[key]
            if entry["expiry"] > asyncio.get_event_loop().time():
                return entry["value"]
            else:
                del self.local_cache[key]
        
        # Check L2 cache (Redis)
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    decoded = orjson.loads(value)
                    # Populate L1 cache
                    self._set_local_cache(key, decoded)
                    return decoded
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set_multi_tier(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        cache_type: str = "default"
    ) -> bool:
        """
        Multi-tier cache set: L1 (local) + L2 (Redis)
        """
        # Determine TTL based on cache type
        if ttl is None:
            ttl = self.cache_ttls.get(cache_type, 300)
        
        # Set in L1 cache
        self._set_local_cache(key, value, min(ttl, self.local_cache_ttl))
        
        # Set in L2 cache (Redis)
        if self.redis_client:
            try:
                serialized = orjson.dumps(value)
                await self.redis_client.setex(key, ttl, serialized)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        return False
    
    def _set_local_cache(self, key: str, value: Any, ttl: int = None):
        """Set value in local cache with TTL"""
        if ttl is None:
            ttl = self.local_cache_ttl
            
        # Implement simple LRU if cache is full
        if len(self.local_cache) >= self.max_local_cache_size:
            self._evict_local_cache()
        
        self.local_cache[key] = {
            "value": value,
            "expiry": asyncio.get_event_loop().time() + ttl,
            "accessed": asyncio.get_event_loop().time()
        }
    
    def _evict_local_cache(self):
        """Evict oldest entries from local cache"""
        current_time = asyncio.get_event_loop().time()
        
        # Remove expired entries first
        expired = [k for k, v in self.local_cache.items() 
                  if v["expiry"] < current_time]
        for key in expired:
            del self.local_cache[key]
        
        # If still over limit, remove least recently accessed
        if len(self.local_cache) >= self.max_local_cache_size:
            sorted_keys = sorted(
                self.local_cache.keys(),
                key=lambda k: self.local_cache[k]["accessed"]
            )
            # Remove 20% of cache
            for key in sorted_keys[:len(sorted_keys) // 5]:
                del self.local_cache[key]
    
    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None,
        cache_type: str = "default"
    ) -> Any:
        """Get from cache or compute and cache result"""
        # Try to get from cache
        cached = await self.get_multi_tier(key)
        if cached is not None:
            return cached
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache the result
        if value is not None:
            await self.set_multi_tier(key, value, ttl, cache_type)
        
        return value
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # Clear from local cache
        keys_to_delete = [k for k in self.local_cache.keys() 
                         if pattern in k or k.startswith(pattern)]
        for key in keys_to_delete:
            del self.local_cache[key]
        
        # Clear from Redis
        if self.redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match=f"{pattern}*", count=100
                    )
                    if keys:
                        await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Pattern invalidation error: {e}")
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get multiple keys efficiently"""
        result = {}
        
        # Check local cache first
        redis_keys = []
        for key in keys:
            if key in self.local_cache:
                entry = self.local_cache[key]
                if entry["expiry"] > asyncio.get_event_loop().time():
                    result[key] = entry["value"]
                else:
                    redis_keys.append(key)
            else:
                redis_keys.append(key)
        
        # Batch get from Redis
        if redis_keys and self.redis_client:
            try:
                values = await self.redis_client.mget(redis_keys)
                for key, value in zip(redis_keys, values):
                    if value:
                        decoded = orjson.loads(value)
                        result[key] = decoded
                        self._set_local_cache(key, decoded)
            except Exception as e:
                logger.error(f"Batch get error: {e}")
        
        return result
    
    async def increment_counter(
        self,
        key: str,
        amount: int = 1,
        ttl: int = 3600
    ) -> int:
        """Atomic counter increment with TTL"""
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incrby(key, amount)
                pipe.expire(key, ttl)
                results = await pipe.execute()
                return results[0]
            except Exception as e:
                logger.error(f"Counter increment error: {e}")
        return 0

class CachedQueryOptimizer:
    """
    Query result caching with intelligent invalidation
    """
    
    def __init__(self, cache_manager: OptimizedCacheManager):
        self.cache = cache_manager
        
    def cache_query(
        self,
        cache_type: str,
        ttl: Optional[int] = None,
        key_prefix: Optional[str] = None
    ):
        """
        Decorator for caching database query results
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_prefix:
                    cache_key = f"{key_prefix}:{self._make_key(*args, **kwargs)}"
                else:
                    cache_key = f"query:{func.__name__}:{self._make_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached = await self.cache.get_multi_tier(cache_key)
                if cached is not None:
                    return cached
                
                # Execute query
                result = await func(*args, **kwargs)
                
                # Cache result
                if result is not None:
                    await self.cache.set_multi_tier(
                        cache_key, result, ttl, cache_type
                    )
                
                return result
            
            return wrapper
        return decorator
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_parts = []
        
        # Add args (skip 'self' if present)
        for arg in args:
            if hasattr(arg, '__class__') and arg.__class__.__name__ in ['AsyncSession']:
                continue
            if hasattr(arg, 'id'):
                key_parts.append(f"{arg.__class__.__name__}:{arg.id}")
            else:
                key_parts.append(str(arg))
        
        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            return hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string

# Singleton instances
cache_manager = OptimizedCacheManager()
query_optimizer = CachedQueryOptimizer(cache_manager)

# Pre-warming strategies
async def warm_cache(db_session):
    """Pre-warm cache with frequently accessed data"""
    logger.info("Starting cache warming...")
    
    # Warm pricing rules cache
    from backend.models import PricingRule, SubscriptionPlan
    
    plans = await db_session.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
    )
    
    for plan in plans.scalars():
        rules = await db_session.execute(
            select(PricingRule).where(
                PricingRule.plan_id == plan.id,
                PricingRule.is_active == True
            )
        )
        
        cache_key = f"pricing_rules:{plan.id}"
        await cache_manager.set_multi_tier(
            cache_key,
            [rule.to_dict() for rule in rules.scalars()],
            cache_type="pricing_rules"
        )
    
    logger.info("Cache warming completed")
