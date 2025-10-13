"""
Cache management module for ValueVerse Billing System
Implements Redis-based caching with fallback to in-memory cache
"""

import os
import json
import asyncio
import logging
from typing import Any, Optional, Union, Dict
from datetime import timedelta
from functools import wraps
import hashlib

import redis.asyncio as redis
from redis.exceptions import RedisError
import orjson

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Redis-based cache manager with in-memory fallback
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://:redispassword123@localhost:6379/0"
        )
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Failed to connect to Redis, using in-memory cache: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self._connected and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return orjson.loads(value)
            except (RedisError, json.JSONDecodeError) as e:
                logger.error(f"Cache get error for key {key}: {e}")
        
        # Fallback to in-memory cache
        if key in self.in_memory_cache:
            cached = self.in_memory_cache[key]
            if cached.get("expiry", float('inf')) > asyncio.get_event_loop().time():
                return cached["value"]
            else:
                del self.in_memory_cache[key]
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        serialized = orjson.dumps(value).decode('utf-8')
        
        if self._connected and self.redis_client:
            try:
                if ttl:
                    if isinstance(ttl, timedelta):
                        ttl = int(ttl.total_seconds())
                    await self.redis_client.setex(key, ttl, serialized)
                else:
                    await self.redis_client.set(key, serialized)
                return True
            except RedisError as e:
                logger.error(f"Cache set error for key {key}: {e}")
        
        # Fallback to in-memory cache
        expiry = None
        if ttl:
            if isinstance(ttl, timedelta):
                ttl = ttl.total_seconds()
            expiry = asyncio.get_event_loop().time() + ttl
        
        self.in_memory_cache[key] = {
            "value": value,
            "expiry": expiry
        }
        
        # Clean up expired entries periodically
        if len(self.in_memory_cache) > 1000:
            await self._cleanup_in_memory_cache()
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        deleted = False
        
        if self._connected and self.redis_client:
            try:
                result = await self.redis_client.delete(key)
                deleted = result > 0
            except RedisError as e:
                logger.error(f"Cache delete error for key {key}: {e}")
        
        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
            deleted = True
        
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self._connected and self.redis_client:
            try:
                return await self.redis_client.exists(key) > 0
            except RedisError as e:
                logger.error(f"Cache exists error for key {key}: {e}")
        
        if key in self.in_memory_cache:
            cached = self.in_memory_cache[key]
            if cached.get("expiry", float('inf')) > asyncio.get_event_loop().time():
                return True
            else:
                del self.in_memory_cache[key]
        
        return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache"""
        if self._connected and self.redis_client:
            try:
                return await self.redis_client.incrby(key, amount)
            except RedisError as e:
                logger.error(f"Cache increment error for key {key}: {e}")
        
        # Fallback to in-memory
        current = await self.get(key) or 0
        new_value = current + amount
        await self.set(key, new_value)
        return new_value
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        result = {}
        
        if self._connected and self.redis_client:
            try:
                values = await self.redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        result[key] = orjson.loads(value)
            except (RedisError, json.JSONDecodeError) as e:
                logger.error(f"Cache get_many error: {e}")
        
        # Fallback to in-memory for missing keys
        for key in keys:
            if key not in result and key in self.in_memory_cache:
                cached = self.in_memory_cache[key]
                if cached.get("expiry", float('inf')) > asyncio.get_event_loop().time():
                    result[key] = cached["value"]
        
        return result
    
    async def flush_all(self):
        """Clear all cache entries (use with caution!)"""
        if self._connected and self.redis_client:
            try:
                await self.redis_client.flushdb()
            except RedisError as e:
                logger.error(f"Cache flush error: {e}")
        
        self.in_memory_cache.clear()
    
    async def _cleanup_in_memory_cache(self):
        """Remove expired entries from in-memory cache"""
        current_time = asyncio.get_event_loop().time()
        expired_keys = [
            key for key, cached in self.in_memory_cache.items()
            if cached.get("expiry") and cached["expiry"] < current_time
        ]
        for key in expired_keys:
            del self.in_memory_cache[key]
    
    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            return hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string

def cached(
    ttl: Union[int, timedelta] = 300,
    key_prefix: Optional[str] = None,
    cache_none: bool = False
):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds or timedelta
        key_prefix: Optional prefix for cache keys
        cache_none: Whether to cache None results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{CacheManager.make_key(*args, **kwargs)}"
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{CacheManager.make_key(*args, **kwargs)}"
            
            # Try to get from cache
            cache_manager = kwargs.pop("cache_manager", None) or cache_manager_instance
            cached_value = await cache_manager.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
            
            # Call the function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if result is not None or cache_none:
                await cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator

# Global cache manager instance
cache_manager_instance = CacheManager()

# Cache key patterns for different data types
class CacheKeys:
    """Standard cache key patterns"""
    
    USAGE_SUMMARY = "usage:summary:{organization_id}:{start_date}:{end_date}"
    INVOICE = "invoice:{invoice_id}"
    SUBSCRIPTION = "subscription:{subscription_id}"
    PRICING_RULES = "pricing:rules:{plan_id}"
    ORGANIZATION = "org:{organization_id}"
    PAYMENT_METHOD = "payment:{payment_method_id}"
    RATE_LIMIT = "rate_limit:{user_id}"
    
    @staticmethod
    def format(pattern: str, **kwargs) -> str:
        """Format a cache key pattern with values"""
        return pattern.format(**kwargs)
