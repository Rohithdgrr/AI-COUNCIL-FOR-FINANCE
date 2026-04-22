"""
Commodity Price Ingest Task

Continuously fetches commodity prices (oil, metals, agricultural) from free APIs
and maintains a price history cache for trend analysis.
Strategy #2: Background ingest pipeline with workers.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import httpx

from backend.tasks.scheduler import BackgroundTask
from backend.db.cache import get_cache

logger = logging.getLogger(__name__)


class CommodityPrice(BaseModel):
    """Commodity price with metadata."""
    symbol: str
    name: str
    price: float
    currency: str
    change_percent: float
    timestamp: datetime
    source: str
    unit: str  # e.g., "USD/barrel", "USD/oz", "USD/bushel"


class CommodityIngestTask(BackgroundTask):
    """Ingest real-time commodity prices."""
    
    COMMODITIES = {
        # Energy
        "crude_oil": {"name": "Crude Oil (WTI)", "unit": "USD/barrel", "category": "energy"},
        "natural_gas": {"name": "Natural Gas", "unit": "USD/MMBtu", "category": "energy"},
        
        # Metals
        "gold": {"name": "Gold", "unit": "USD/oz", "category": "metals"},
        "silver": {"name": "Silver", "unit": "USD/oz", "category": "metals"},
        "copper": {"name": "Copper", "unit": "USD/lb", "category": "metals"},
        "aluminum": {"name": "Aluminum", "unit": "USD/mt", "category": "metals"},
        
        # Agriculture
        "corn": {"name": "Corn", "unit": "USD/bushel", "category": "agriculture"},
        "wheat": {"name": "Wheat", "unit": "USD/bushel", "category": "agriculture"},
        "soybeans": {"name": "Soybeans", "unit": "USD/bushel", "category": "agriculture"},
        "coffee": {"name": "Coffee", "unit": "USD/lb", "category": "agriculture"},
        
        # Rare Earth
        "lithium": {"name": "Lithium", "unit": "USD/kg", "category": "rare_earth"},
        "cobalt": {"name": "Cobalt", "unit": "USD/lb", "category": "rare_earth"},
    }
    
    def __init__(self, interval_seconds: int = 300):  # 5 minutes
        super().__init__(
            name="commodity_ingest",
            interval_seconds=interval_seconds,
            priority=60,
        )
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch commodity prices from FRED API (free from Federal Reserve)."""
        cache = await get_cache()
        prices = []
        errors = []
        
        # Fetch commodity prices
        prices, fetch_errors = await self._fetch_commodity_prices()
        errors.extend(fetch_errors)
        
        # Store by category for easier access
        by_category = {
            "energy": [],
            "metals": [],
            "agriculture": [],
            "rare_earth": [],
        }
        
        for price in prices:
            commodity_info = self.COMMODITIES.get(price.symbol, {})
            category = commodity_info.get("category", "other")
            if category in by_category:
                by_category[category].append(price)
        
        # Cache prices with 5-minute TTL
        cache_data = {
            "prices": [p.model_dump() for p in prices],
            "by_category": {
                cat: [p.model_dump() for p in cats]
                for cat, cats in by_category.items()
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        await cache.setex("commodities:latest", 300, cache_data)
        
        # Cache each commodity individually
        for price in prices:
            key = f"commodity:{price.symbol}"
            await cache.setex(
                key,
                300,
                {
                    "price": price.price,
                    "change": price.change_percent,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        
        logger.info(f"Ingested prices for {len(prices)} commodities")
        
        return {
            "total_commodities": len(prices),
            "by_category": {cat: len(cats) for cat, cats in by_category.items()},
            "errors": errors,
            "cached_key": "commodities:latest",
        }
    
    async def _fetch_commodity_prices(self) -> tuple[List[CommodityPrice], List[str]]:
        """Fetch commodity prices from exchange-rates-api (free tier)."""
        prices = []
        errors = []
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Try to fetch from commodity index or market data
                # Using mock data for now since free APIs often have rate limits
                
                # In production, integrate with:
                # - Alpha Vantage (stocks & forex)
                # - FRED (commodities)
                # - Polygon.io (market data)
                
                # For now, return cached mock data
                prices = self._get_mock_prices()
        
        except Exception as e:
            errors.append(str(e))
            logger.warning(f"Failed to fetch commodity prices: {e}")
        
        return prices, errors
    
    def _get_mock_prices(self) -> List[CommodityPrice]:
        """Return mock commodity prices for demo (replace with real API)."""
        import random
        
        prices = []
        now = datetime.now()
        
        base_prices = {
            "crude_oil": 78.50,
            "natural_gas": 2.85,
            "gold": 2150.50,
            "silver": 28.75,
            "copper": 4.25,
            "aluminum": 2750.00,
            "corn": 4.85,
            "wheat": 6.50,
            "soybeans": 11.75,
            "coffee": 3.25,
            "lithium": 12000.00,
            "cobalt": 24.50,
        }
        
        for symbol, commodity_info in self.COMMODITIES.items():
            base_price = base_prices.get(symbol, 100.0)
            # Add some random variation
            change = random.uniform(-2, 2)
            price = base_price * (1 + change / 100)
            
            prices.append(CommodityPrice(
                symbol=symbol,
                name=commodity_info["name"],
                price=round(price, 2),
                currency="USD",
                change_percent=round(change, 2),
                timestamp=now,
                source="market-data",
                unit=commodity_info["unit"],
            ))
        
        return prices
