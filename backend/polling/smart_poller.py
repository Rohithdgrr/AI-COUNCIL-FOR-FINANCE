"""
Smart Polling with ETags and Conditional Requests

Reduce bandwidth and API load by using HTTP caching headers:
- ETag (Entity Tag) for change detection
- If-Modified-Since for timestamp-based caching
- 304 Not Modified responses
Strategy #5: Poll smarter, not harder.
"""

import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class SmartPoller:
    """Manage HTTP caching headers for efficient polling."""
    
    def __init__(self):
        # Store per-URL: (etag, last_modified, last_data)
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    async def fetch_with_cache(
        self,
        url: str,
        timeout: int = 10,
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Fetch URL with smart caching.
        
        Returns: (data, was_changed)
            - data: Response data or None if not modified
            - was_changed: True if new data, False if 304 Not Modified
        """
        headers = {}
        
        # Add conditional request headers if we have cached data
        if url in self.cache:
            cached = self.cache[url]
            if "etag" in cached:
                headers["If-None-Match"] = cached["etag"]
            if "last_modified" in cached:
                headers["If-Modified-Since"] = cached["last_modified"]
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
            
            # 304 Not Modified - use cached data
            if response.status_code == 304:
                logger.debug(f"Cache hit (304) for {url}")
                if url in self.cache:
                    return self.cache[url].get("data"), False
                return None, False
            
            # 200 OK - new data
            if response.status_code == 200:
                data = response.json()
                
                # Store new cache headers
                cache_entry = {"data": data}
                
                if "etag" in response.headers:
                    cache_entry["etag"] = response.headers["etag"]
                
                if "last-modified" in response.headers:
                    cache_entry["last_modified"] = response.headers["last-modified"]
                
                if "cache-control" in response.headers:
                    cache_entry["cache_control"] = response.headers["cache-control"]
                
                self.cache[url] = cache_entry
                
                logger.debug(f"Cache miss (200) for {url}")
                return data, True
            
            # Other status codes
            logger.warning(f"Unexpected status {response.status_code} for {url}")
            return None, True
        
        except Exception as e:
            logger.error(f"Fetch failed for {url}: {e}")
            
            # Return stale data if available
            if url in self.cache:
                return self.cache[url].get("data"), False
            
            raise
    
    def clear_cache(self, url: Optional[str] = None) -> None:
        """Clear cache for a URL or all URLs."""
        if url:
            self.cache.pop(url, None)
            logger.debug(f"Cleared cache for {url}")
        else:
            self.cache.clear()
            logger.debug("Cleared all caches")


class ConditionalApiPoller:
    """Smart poller for API data with cadence control."""
    
    # Per-source polling cadence (seconds)
    POLLING_CADENCE = {
        "stock_tickers": 15,         # Fast-changing
        "commodity_prices": 60,      # Medium
        "news": 300,                 # Slow-changing
        "weather": 600,              # Very slow-changing
        "forex": 120,                # Medium
        "risk_alerts": 30,           # Fast
    }
    
    def __init__(self):
        self.poller = SmartPoller()
        self.last_fetch: Dict[str, float] = {}
    
    async def poll_if_ready(
        self,
        source_key: str,
        url: str,
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Poll only if cadence interval has passed.
        
        Returns: (data, was_changed)
        """
        import time
        
        now = time.time()
        last_fetch = self.last_fetch.get(source_key, 0)
        cadence = self.POLLING_CADENCE.get(source_key, 300)
        
        elapsed = now - last_fetch
        
        # Not yet ready to poll
        if elapsed < cadence:
            logger.debug(
                f"{source_key}: Skipping poll (fetched {elapsed:.0f}s ago, "
                f"cadence {cadence}s)"
            )
            return None, False
        
        # Ready to poll
        self.last_fetch[source_key] = now
        
        try:
            data, was_changed = await self.poller.fetch_with_cache(url)
            
            if was_changed:
                logger.info(f"{source_key}: New data fetched")
            else:
                logger.debug(f"{source_key}: No changes (304)")
            
            return data, was_changed
        
        except Exception as e:
            logger.error(f"{source_key}: Poll failed - {e}")
            raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_urls = len(self.poller.cache)
        cached_sizes = sum(
            len(str(entry.get("data", "")))
            for entry in self.poller.cache.values()
        )
        
        return {
            "cached_urls": total_urls,
            "total_size_bytes": cached_sizes,
            "avg_size_bytes": cached_sizes // max(total_urls, 1),
            "etag_count": sum(
                1 for entry in self.poller.cache.values()
                if "etag" in entry
            ),
            "last_modified_count": sum(
                1 for entry in self.poller.cache.values()
                if "last_modified" in entry
            ),
        }


# Global smart poller instance
_global_poller: Optional[ConditionalApiPoller] = None


def get_smart_poller() -> ConditionalApiPoller:
    """Get or create global smart poller."""
    global _global_poller
    if _global_poller is None:
        _global_poller = ConditionalApiPoller()
    return _global_poller
