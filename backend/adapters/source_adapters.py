"""
Source-Specific Adapter Framework

Pluggable adapters for each data source type:
- REST API adapters
- Webhook adapters  
- Streaming WebSocket adapters
- RSS feed adapters
- File-based adapters

Makes it easy to add new sources without modifying core code.
Strategy #9: Add source-specific adapters.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """Type of data source."""
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    RSS_FEED = "rss_feed"
    FILE_BASED = "file_based"
    POLLING = "polling"


class SourceAdapter(ABC):
    """Base class for all data source adapters."""
    
    def __init__(self, name: str, source_type: SourceType, config: Dict[str, Any]):
        self.name = name
        self.source_type = source_type
        self.config = config
        self.last_fetch_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Fetch data from source."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to source."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "name": self.name,
            "type": self.source_type.value,
            "last_fetch": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "last_error": self.last_error,
        }


class RestApiAdapter(SourceAdapter):
    """Adapter for REST API sources."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
    ):
        super().__init__(name, SourceType.REST_API, config)
        # config should have: url, method, headers, params, timeout
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Fetch from REST API."""
        try:
            import httpx
            
            url = self.config.get("url")
            method = self.config.get("method", "GET").upper()
            headers = self.config.get("headers", {})
            params = self.config.get("params", {})
            timeout = self.config.get("timeout", 10)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=params)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                
                self.last_fetch_time = datetime.now()
                self.last_error = None
                
                return response.json()
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"RestApiAdapter {self.name} failed: {e}")
            return None
    
    async def validate_connection(self) -> bool:
        """Validate API connectivity."""
        try:
            import httpx
            
            url = self.config.get("url")
            timeout = self.config.get("timeout", 5)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(url)
                return response.status_code < 400
        
        except Exception as e:
            logger.warning(f"Connection validation failed for {self.name}: {e}")
            return False


class RssFeedAdapter(SourceAdapter):
    """Adapter for RSS/Atom feeds."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
    ):
        super().__init__(name, SourceType.RSS_FEED, config)
        # config should have: feed_url, max_entries
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Fetch from RSS feed."""
        try:
            import httpx
            import feedparser
            
            feed_url = self.config.get("feed_url")
            max_entries = self.config.get("max_entries", 10)
            timeout = self.config.get("timeout", 10)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            entries = feed.entries[:max_entries]
            
            items = []
            for entry in entries:
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:500],
                })
            
            self.last_fetch_time = datetime.now()
            self.last_error = None
            
            return {
                "feed_title": feed.feed.get("title", ""),
                "entries": items,
                "count": len(items),
            }
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"RssFeedAdapter {self.name} failed: {e}")
            return None
    
    async def validate_connection(self) -> bool:
        """Validate feed accessibility."""
        try:
            import httpx
            
            feed_url = self.config.get("feed_url")
            timeout = self.config.get("timeout", 5)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(feed_url)
                return response.status_code < 400
        
        except Exception as e:
            logger.warning(f"Feed validation failed for {self.name}: {e}")
            return False


class WebhookAdapter(SourceAdapter):
    """Adapter for receiving webhook data."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
    ):
        super().__init__(name, SourceType.WEBHOOK, config)
        # config should have: endpoint, secret
        self._pending_events: List[Dict] = []
    
    async def receive_webhook(self, payload: Dict[str, Any]) -> None:
        """Receive webhook data."""
        self._pending_events.append({
            "payload": payload,
            "received_at": datetime.now().isoformat(),
        })
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Get pending webhook events."""
        if not self._pending_events:
            return None
        
        events = self._pending_events
        self._pending_events = []
        
        self.last_fetch_time = datetime.now()
        self.last_error = None
        
        return {
            "events": events,
            "count": len(events),
        }
    
    async def validate_connection(self) -> bool:
        """Webhook adapters are always 'connected'."""
        return True


class PollingAdapter(SourceAdapter):
    """Adapter for polling-based data sources."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
    ):
        super().__init__(name, SourceType.POLLING, config)
        # config should have: fetch_function, interval_seconds
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Poll data source."""
        try:
            import asyncio
            
            fetch_fn = self.config.get("fetch_function")
            if not fetch_fn:
                raise ValueError("fetch_function not provided in config")
            
            if asyncio.iscoroutinefunction(fetch_fn):
                data = await fetch_fn()
            else:
                data = fetch_fn()
            
            self.last_fetch_time = datetime.now()
            self.last_error = None
            
            return data
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"PollingAdapter {self.name} failed: {e}")
            return None
    
    async def validate_connection(self) -> bool:
        """Validate polling function."""
        return True


class AdapterRegistry:
    """Registry and factory for data source adapters."""
    
    def __init__(self):
        self.adapters: Dict[str, SourceAdapter] = {}
    
    def register_adapter(self, adapter: SourceAdapter) -> None:
        """Register a data source adapter."""
        self.adapters[adapter.name] = adapter
        logger.info(f"Registered adapter: {adapter.name} ({adapter.source_type.value})")
    
    def create_rest_adapter(self, name: str, url: str, **kwargs) -> RestApiAdapter:
        """Factory for REST API adapters."""
        config = {
            "url": url,
            "method": kwargs.get("method", "GET"),
            "headers": kwargs.get("headers", {}),
            "params": kwargs.get("params", {}),
            "timeout": kwargs.get("timeout", 10),
        }
        adapter = RestApiAdapter(name, config)
        self.register_adapter(adapter)
        return adapter
    
    def create_rss_adapter(self, name: str, feed_url: str, **kwargs) -> RssFeedAdapter:
        """Factory for RSS feed adapters."""
        config = {
            "feed_url": feed_url,
            "max_entries": kwargs.get("max_entries", 10),
            "timeout": kwargs.get("timeout", 10),
        }
        adapter = RssFeedAdapter(name, config)
        self.register_adapter(adapter)
        return adapter
    
    def create_webhook_adapter(self, name: str, endpoint: str, **kwargs) -> WebhookAdapter:
        """Factory for webhook adapters."""
        config = {
            "endpoint": endpoint,
            "secret": kwargs.get("secret", ""),
        }
        adapter = WebhookAdapter(name, config)
        self.register_adapter(adapter)
        return adapter
    
    def create_polling_adapter(
        self,
        name: str,
        fetch_function,
        **kwargs
    ) -> PollingAdapter:
        """Factory for polling adapters."""
        config = {
            "fetch_function": fetch_function,
            "interval_seconds": kwargs.get("interval_seconds", 300),
        }
        adapter = PollingAdapter(name, config)
        self.register_adapter(adapter)
        return adapter
    
    async def validate_all(self) -> Dict[str, bool]:
        """Validate all registered adapters."""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                results[name] = await adapter.validate_connection()
            except Exception as e:
                logger.error(f"Validation failed for {name}: {e}")
                results[name] = False
        return results
    
    def get_adapter(self, name: str) -> Optional[SourceAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)
    
    def get_status_all(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all adapters."""
        return {
            name: adapter.get_status()
            for name, adapter in self.adapters.items()
        }


# Global adapter registry
_adapter_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """Get or create global adapter registry."""
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry()
    return _adapter_registry
