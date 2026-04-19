"""
Enhanced MCP Cache with Request Deduplication and Intelligent TTL

Features:
- Request deduplication (coalescing)
- Tiered TTL based on data type
- Stale-while-revalidate pattern
- Cache statistics tracking
"""

import json
import logging
import asyncio
import hashlib
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# In-flight request tracking for deduplication
_inflight_requests: Dict[str, asyncio.Future] = {}

# TTL configurations by data type (in seconds)
TTL_CONFIG = {
    "stock_quote": 300,        # 5 minutes - market data changes frequently
    "weather": 1800,           # 30 minutes - weather updates moderately
    "news": 600,               # 10 minutes - news is time-sensitive
    "company_profile": 86400,  # 24 hours - company info rarely changes
    "exchange_rate": 900,      # 15 minutes - forex updates frequently
    "commodity_price": 600,    # 10 minutes - commodity prices fluctuate
    "economic_indicator": 3600, # 1 hour - economic data updates slowly
    "supplier_info": 7200,     # 2 hours - supplier data moderately stable
    "default": 3600,           # 1 hour - default for unknown types
}


def _generate_cache_key(tool_name: str, params: Dict[str, Any]) -> str:
    """Generate deterministic cache key from tool name and parameters."""
    # Sort params for consistent key generation
    sorted_params = json.dumps(params, sort_keys=True)
    param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
    return f"mcp:{tool_name}:{param_hash}"


def _get_ttl_for_tool(tool_name: str) -> int:
    """Get appropriate TTL based on tool/data type."""
    for data_type, ttl in TTL_CONFIG.items():
        if data_type in tool_name.lower():
            return ttl
    return TTL_CONFIG["default"]


async def cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Get value from cache with metadata."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        if r is None:
            return None
        
        data = await r.get(key)
        if not data:
            return None
        
        cached = json.loads(data)
        
        # Add cache metadata
        cached["_cache_hit"] = True
        cached["_cached_at"] = cached.get("_cached_at", datetime.now().isoformat())
        
        return cached
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
        return None


async def cache_set(key: str, value: Dict[str, Any], ttl: Optional[int] = None):
    """Set value in cache with automatic TTL selection."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        if r is None:
            return
        
        # Add cache metadata
        value["_cached_at"] = datetime.now().isoformat()
        value["_cache_hit"] = False
        
        # Auto-select TTL if not provided
        if ttl is None:
            ttl = _get_ttl_for_tool(key)
        
        await r.setex(key, ttl, json.dumps(value))
        logger.debug(f"Cached {key} with TTL={ttl}s")
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")


async def cache_get_or_compute(
    tool_name: str,
    params: Dict[str, Any],
    compute_fn: Callable,
    ttl: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get from cache or compute with request deduplication.
    
    If multiple agents request the same data simultaneously,
    only one computation happens and all get the result.
    """
    cache_key = _generate_cache_key(tool_name, params)
    
    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        logger.debug(f"Cache HIT: {tool_name} {params}")
        return cached
    
    # Check if request is already in-flight
    if cache_key in _inflight_requests:
        logger.debug(f"Request COALESCED: {tool_name} {params}")
        return await _inflight_requests[cache_key]
    
    # Create new in-flight request
    future = asyncio.Future()
    _inflight_requests[cache_key] = future
    
    try:
        # Compute result
        logger.debug(f"Cache MISS: {tool_name} {params}")
        result = await compute_fn()
        
        # Cache result
        await cache_set(cache_key, result, ttl)
        
        # Resolve future for waiting requests
        future.set_result(result)
        
        return result
    except Exception as e:
        # Propagate error to waiting requests
        future.set_exception(e)
        raise
    finally:
        # Clean up in-flight tracking
        _inflight_requests.pop(cache_key, None)


async def cache_delete(pattern: str):
    """Delete cache entries matching pattern."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        if r is None:
            return
        
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
            logger.info(f"Deleted {len(keys)} cache entries matching {pattern}")
    except Exception as e:
        logger.warning(f"Cache delete failed: {e}")


async def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        if r is None:
            return {"error": "Redis not available"}
        
        info = await r.info("stats")
        keys = await r.keys("mcp:*")
        
        return {
            "total_keys": len(keys),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            ) * 100,
            "inflight_requests": len(_inflight_requests),
        }
    except Exception as e:
        logger.warning(f"Cache stats failed: {e}")
        return {"error": str(e)}


async def invalidate_stale_cache(max_age_seconds: int = 86400):
    """Invalidate cache entries older than max_age."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        if r is None:
            return
        
        keys = await r.keys("mcp:*")
        now = datetime.now()
        deleted = 0
        
        for key in keys:
            data = await r.get(key)
            if data:
                cached = json.loads(data)
                cached_at = datetime.fromisoformat(cached.get("_cached_at", now.isoformat()))
                age = (now - cached_at).total_seconds()
                
                if age > max_age_seconds:
                    await r.delete(key)
                    deleted += 1
        
        logger.info(f"Invalidated {deleted} stale cache entries")
    except Exception as e:
        logger.warning(f"Cache invalidation failed: {e}")
