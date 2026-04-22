"""
Real-time News Ingestion Task

Continuously fetches latest news from multiple sources and caches results.
Supports RSS feeds from Google News, Reuters, and sector-specific sources.
Strategy #8: RSS and structured feeds for "live enough" news.
"""

import asyncio
import feedparser
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import httpx

from backend.tasks.scheduler import BackgroundTask
from backend.db.cache import get_cache

logger = logging.getLogger(__name__)


class NewsItem(BaseModel):
    """News article."""
    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    category: Optional[str] = None


class NewsIngestTask(BackgroundTask):
    """Ingest news from multiple sources."""
    
    # RSS feeds from reliable sources
    NEWS_SOURCES = {
        "reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&output=rss",
        "gdacs": "https://www.gdacs.org/AppData/DisasterRss.xml",  # Disaster alerts
        "google_news": "https://news.google.com/rss?ceid=US:en&q=supply chain",
        "bbc_news": "http://feeds.bbc.co.uk/news/rss.xml",
    }
    
    def __init__(self, interval_seconds: int = 300):  # 5 minutes
        super().__init__(
            name="news_ingest",
            interval_seconds=interval_seconds,
            priority=70,  # High priority
        )
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch and cache news from all sources."""
        cache = await get_cache()
        all_items = []
        errors = []
        
        # Fetch from all sources in parallel
        tasks = [
            self._fetch_source(source_name, feed_url)
            for source_name, feed_url in self.NEWS_SOURCES.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source_name, result in zip(self.NEWS_SOURCES.keys(), results):
            if isinstance(result, Exception):
                errors.append(f"{source_name}: {str(result)}")
                logger.error(f"Failed to fetch {source_name}: {result}")
            else:
                items, error_msg = result
                all_items.extend(items)
                if error_msg:
                    errors.append(f"{source_name}: {error_msg}")
        
        # Sort by published date (newest first)
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        
        # Cache top 50 items with 5-minute TTL
        cache_key = "news:latest:50"
        await cache.setex(
            cache_key,
            300,  # 5 minutes
            {
                "items": [item.model_dump() for item in all_items[:50]],
                "timestamp": datetime.now().isoformat(),
                "total_items": len(all_items),
            }
        )
        
        logger.info(f"Ingested {len(all_items)} news items from {len(self.NEWS_SOURCES)} sources")
        
        return {
            "total_items": len(all_items),
            "sources_fetched": len(self.NEWS_SOURCES),
            "errors": errors,
            "cached_key": cache_key,
        }
    
    async def _fetch_source(
        self,
        source_name: str,
        feed_url: str,
    ) -> tuple[List[NewsItem], Optional[str]]:
        """Fetch news from a single RSS source."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(feed_url, follow_redirects=True)
                response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            items = []
            for entry in feed.entries[:10]:  # Limit to 10 per source
                try:
                    published_str = entry.get("published", "")
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else datetime.now()
                    
                    item = NewsItem(
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        source=source_name,
                        published_at=published_at,
                        summary=entry.get("summary", "")[:500],  # Truncate summary
                        category=entry.get("category", ""),
                    )
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse entry from {source_name}: {e}")
            
            return items, None
        
        except Exception as e:
            return [], str(e)
