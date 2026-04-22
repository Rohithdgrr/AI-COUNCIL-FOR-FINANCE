"""
Multi-Source Data Aggregation per Dashboard Widget

Each widget can pull from multiple sources with priority ranking,
fallback mechanisms, and intelligent merging.
Strategy #6: Aggregate multiple sources per widget.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SourcePriority(int, Enum):
    """Priority ranking for data sources."""
    PRIMARY = 1        # First choice
    FALLBACK = 2       # Backup if primary fails
    SUPPLEMENT = 3     # Additional context


class DataSource:
    """Single data source for a widget."""
    
    def __init__(
        self,
        name: str,
        fetch_fn: Callable,
        priority: SourcePriority = SourcePriority.PRIMARY,
        ttl_seconds: int = 300,
        required: bool = False,
    ):
        self.name = name
        self.fetch_fn = fetch_fn
        self.priority = priority
        self.ttl_seconds = ttl_seconds
        self.required = required  # If True, widget fails without this source
        self.last_data = None
        self.last_fetch_time = None
    
    async def fetch(self) -> Optional[Dict[str, Any]]:
        """Fetch data from this source."""
        try:
            import asyncio
            
            # Call function if async, otherwise just call
            if asyncio.iscoroutinefunction(self.fetch_fn):
                self.last_data = await self.fetch_fn()
            else:
                self.last_data = self.fetch_fn()
            
            self.last_fetch_time = datetime.now()
            return self.last_data
        
        except Exception as e:
            logger.warning(f"Source {self.name} fetch failed: {e}")
            return None


class WidgetAggregator:
    """Aggregate data from multiple sources for a single widget."""
    
    def __init__(self, widget_name: str):
        self.widget_name = widget_name
        self.sources: List[DataSource] = []
    
    def add_source(
        self,
        name: str,
        fetch_fn: Callable,
        priority: SourcePriority = SourcePriority.PRIMARY,
        ttl_seconds: int = 300,
        required: bool = False,
    ) -> None:
        """Register a data source for this widget."""
        source = DataSource(name, fetch_fn, priority, ttl_seconds, required)
        self.sources.append(source)
        
        # Sort by priority
        self.sources.sort(key=lambda s: s.priority.value)
        
        logger.debug(f"Added source {name} to widget {self.widget_name}")
    
    async def fetch_aggregated(self) -> Dict[str, Any]:
        """
        Fetch from all sources and aggregate.
        
        Tries primary first, falls back if needed.
        """
        import asyncio
        
        results = {
            "primary": None,
            "fallback": None,
            "supplementary": [],
            "sources_used": [],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Organize by priority
        primary_sources = [s for s in self.sources if s.priority == SourcePriority.PRIMARY]
        fallback_sources = [s for s in self.sources if s.priority == SourcePriority.FALLBACK]
        supp_sources = [s for s in self.sources if s.priority == SourcePriority.SUPPLEMENT]
        
        # Fetch primary sources
        if primary_sources:
            tasks = [s.fetch() for s in primary_sources]
            primary_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for source, result in zip(primary_sources, primary_results):
                if not isinstance(result, Exception) and result:
                    results["primary"] = result
                    results["sources_used"].append(source.name)
                    break  # Use first successful primary
        
        # If primary failed and fallback available, try fallback
        if not results["primary"] and fallback_sources:
            tasks = [s.fetch() for s in fallback_sources]
            fallback_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for source, result in zip(fallback_sources, fallback_results):
                if not isinstance(result, Exception) and result:
                    results["fallback"] = result
                    results["sources_used"].append(source.name)
                    break
        
        # Always fetch supplementary for enrichment
        if supp_sources:
            tasks = [s.fetch() for s in supp_sources]
            supp_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for source, result in zip(supp_sources, supp_results):
                if not isinstance(result, Exception) and result:
                    results["supplementary"].append({
                        "source": source.name,
                        "data": result,
                    })
                    results["sources_used"].append(source.name)
        
        # Check required sources
        required_sources = [s.name for s in self.sources if s.required]
        used_required = [
            s for s in required_sources
            if s in results["sources_used"]
        ]
        
        if len(used_required) < len(required_sources):
            missing = [s for s in required_sources if s not in results["sources_used"]]
            logger.warning(
                f"Widget {self.widget_name} missing required sources: {missing}"
            )
            results["available"] = False
        else:
            results["available"] = True
        
        # Merge data
        results["data"] = self._merge_data(results)
        
        return results
    
    def _merge_data(self, results: Dict) -> Dict[str, Any]:
        """Intelligently merge data from multiple sources."""
        merged = {}
        
        # Primary data is base
        if results["primary"]:
            merged.update(results["primary"])
        
        # Fallback adds missing fields
        if results["fallback"]:
            for key, value in results["fallback"].items():
                if key not in merged or merged[key] is None:
                    merged[key] = value
        
        # Supplementary enriches
        for supp in results["supplementary"]:
            supp_data = supp.get("data", {})
            for key, value in supp_data.items():
                # Create enriched field name
                enriched_key = f"{supp['source']}_{key}"
                merged[enriched_key] = value
        
        return merged


class DashboardAggregationStrategy:
    """Pre-configured aggregation strategies for common widgets."""
    
    @staticmethod
    def create_market_ticker_aggregator(
        finnhub_fetch: Callable,
        polygon_fetch: Callable,
        cache_fetch: Callable,
    ) -> WidgetAggregator:
        """Market ticker widget: Finnhub primary, Polygon fallback, Cache supplement."""
        agg = WidgetAggregator("market_ticker")
        
        agg.add_source(
            "finnhub",
            finnhub_fetch,
            priority=SourcePriority.PRIMARY,
            ttl_seconds=30,
            required=True,
        )
        
        agg.add_source(
            "polygon",
            polygon_fetch,
            priority=SourcePriority.FALLBACK,
            ttl_seconds=60,
        )
        
        agg.add_source(
            "cache",
            cache_fetch,
            priority=SourcePriority.SUPPLEMENT,
            ttl_seconds=300,
        )
        
        return agg
    
    @staticmethod
    def create_risk_dashboard_aggregator(
        market_fetch: Callable,
        weather_fetch: Callable,
        disaster_fetch: Callable,
    ) -> WidgetAggregator:
        """Risk dashboard: Market primary, Weather + Disaster supplement."""
        agg = WidgetAggregator("risk_dashboard")
        
        agg.add_source(
            "market_risk",
            market_fetch,
            priority=SourcePriority.PRIMARY,
            ttl_seconds= 120,
            required=True,
        )
        
        agg.add_source(
            "weather",
            weather_fetch,
            priority=SourcePriority.SUPPLEMENT,
            ttl_seconds=600,
        )
        
        agg.add_source(
            "disasters",
            disaster_fetch,
            priority=SourcePriority.SUPPLEMENT,
            ttl_seconds=600,
        )
        
        return agg
    
    @staticmethod
    def create_news_widget_aggregator(
        reuters_fetch: Callable,
        google_news_fetch: Callable,
        local_news_fetch: Callable,
    ) -> WidgetAggregator:
        """News widget: Reuters primary, Google News fallback, Local supplement."""
        agg = WidgetAggregator("news_widget")
        
        agg.add_source(
            "reuters",
            reuters_fetch,
            priority=SourcePriority.PRIMARY,
            ttl_seconds=300,
            required=True,
        )
        
        agg.add_source(
            "google_news",
            google_news_fetch,
            priority=SourcePriority.FALLBACK,
            ttl_seconds=300,
        )
        
        agg.add_source(
            "local_news",
            local_news_fetch,
            priority=SourcePriority.SUPPLEMENT,
            ttl_seconds=600,
        )
        
        return agg


# Registry of widget aggregators
_aggregators: Dict[str, WidgetAggregator] = {}


def register_widget_aggregator(widget_name: str, aggregator: WidgetAggregator) -> None:
    """Register a widget aggregator."""
    _aggregators[widget_name] = aggregator
    logger.debug(f"Registered aggregator for widget: {widget_name}")


async def fetch_widget_data(widget_name: str) -> Dict[str, Any]:
    """Fetch aggregated data for a widget."""
    if widget_name not in _aggregators:
        raise ValueError(f"No aggregator registered for widget: {widget_name}")
    
    aggregator = _aggregators[widget_name]
    return await aggregator.fetch_aggregated()
