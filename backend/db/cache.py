"""
Distributed Cache Layer for Real-Time Data

Supports Redis backend with fallback to in-memory cache.
Implements cache warming and stale-while-revalidate patterns.
Strategy #7: Cache warming + stale-while-revalidate.
"""

import logging
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with metadata."""
    
    def __init__(self, value: Any, ttl: int = 300, stale_ttl: int = 600):
        self.value = value
        self.created_at = datetime.now()
        self.ttl = ttl  # Time to live
        self.stale_ttl = stale_ttl  # Time before marked as stale
    
    def is_fresh(self) -> bool:
        """Check if entry is fresh."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age < self.ttl
    
    def is_stale(self) -> bool:
        """Check if entry is stale but usable."""
        age = (datetime.now() - self.created_at).total_seconds()
        return self.ttl <= age < self.stale_ttl
    
    def is_expired(self) -> bool:
        """Check if entry is completely expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age >= self.stale_ttl


class Cache:
    """Abstract cache interface."""
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache."""
        raise NotImplementedError
    
    async def setex(self, key: str, ttl: int, value: Any) -> None:
        """Set value with TTL (alias for set)."""
        await self.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete from cache."""
        raise NotImplementedError
    
    async def clear(self) -> None:
        """Clear entire cache."""
        raise NotImplementedError
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_fn,
        ttl: int = 300,
        stale_ttl: int = 600,
    ) -> Any:
        """Get from cache or fetch and cache - stale-while-revalidate pattern."""
        cached = await self.get(key)
        
        if cached is not None:
            entry = cached if isinstance(cached, CacheEntry) else CacheEntry(cached, ttl, stale_ttl)
            
            if entry.is_fresh():
                # Return fresh data
                return entry.value
            
            elif entry.is_stale():
                # Return stale data immediately, refresh in background
                asyncio.create_task(self._refresh_background(key, fetch_fn, ttl, stale_ttl))
                return entry.value
        
        # Fetch new data
        try:
            value = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()
            await self.set(key, value, ttl)
            return value
        except Exception as e:
            # If fetch fails and we have stale data, return that
            if cached:
                entry = cached if isinstance(cached, CacheEntry) else CacheEntry(cached, ttl, stale_ttl)
                if not entry.is_expired():
                    logger.warning(f"Fetch failed for {key}, returning stale data: {e}")
                    return entry.value
            raise
    
    async def _refresh_background(self, key: str, fetch_fn, ttl: int, stale_ttl: int) -> None:
        """Refresh cache in background."""
        try:
            value = await fetch_fn() if asyncio.iscoroutinefunction(fetch_fn) else fetch_fn()
            await self.set(key, value, ttl)
        except Exception as e:
            logger.warning(f"Background refresh failed for {key}: {e}")


class InMemoryCache(Cache):
    """Simple in-memory cache."""
    
    def __init__(self):
        self.data: Dict[str, CacheEntry] = {}
    
    async def get(self, key: str) -> Any:
        """Get from memory."""
        entry = self.data.get(key)
        if not entry:
            return None
        
        if entry.is_expired():
            del self.data[key]
            return None
        
        return entry
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set in memory."""
        self.data[key] = CacheEntry(value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete from memory."""
        self.data.pop(key, None)
    
    async def clear(self) -> None:
        """Clear memory."""
        self.data.clear()


class RedisCache(Cache):
    """Redis-backed cache with fallback to in-memory."""
    
    def __init__(self, redis_client=None, fallback: bool = True):
        self.redis = redis_client
        self.fallback = fallback
        self._memory_cache = InMemoryCache() if fallback else None
    
    async def get(self, key: str) -> Any:
        """Get from Redis or memory."""
        try:
            if not self.redis:
                if self._memory_cache:
                    return await self._memory_cache.get(key)
                return None
            
            value = await self.redis.get(key)
            if value:
                # Deserialize from JSON
                return json.loads(value)
            return None
        
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
            if self._memory_cache:
                return await self._memory_cache.get(key)
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set in Redis or memory."""
        try:
            if not self.redis:
                if self._memory_cache:
                    await self._memory_cache.set(key, value, ttl)
                return
            
            # Serialize to JSON
            json_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, json_value)
        
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")
            if self._memory_cache:
                await self._memory_cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        """Delete from Redis or memory."""
        try:
            if self.redis:
                await self.redis.delete(key)
            if self._memory_cache:
                await self._memory_cache.delete(key)
        except Exception as e:
            logger.warning(f"Delete failed for {key}: {e}")
    
    async def clear(self) -> None:
        """Clear Redis or memory."""
        try:
            if self.redis:
                await self.redis.flushdb()
            if self._memory_cache:
                await self._memory_cache.clear()
        except Exception as e:
            logger.warning(f"Clear failed: {e}")


# Global cache instance
_cache_instance: Optional[Cache] = None


async def init_cache(redis_client=None) -> Cache:
    """Initialize global cache."""
    global _cache_instance
    
    if redis_client:
        _cache_instance = RedisCache(redis_client, fallback=True)
        logger.info("RedisCache initialized with fallback")
    else:
        _cache_instance = InMemoryCache()
        logger.info("InMemoryCache initialized")
    
    return _cache_instance


async def get_cache() -> Cache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        await init_cache()
    return _cache_instance
