"""
Vendor Streaming API Adapters

Integrate with Finnhub, Polygon, and other vendor streaming endpoints
for real-time stock quotes, forex, and commodity data.
Strategy #3: Prefer provider streaming APIs where available.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel
from datetime import datetime
import httpx

from backend.tasks.scheduler import BackgroundTask
from backend.db.cache import get_cache

logger = logging.getLogger(__name__)


class StreamAdapter(BaseModel):
    """Stock/market price with streaming source."""
    symbol: str
    price: float
    change: float
    change_percent: float
    timestamp: datetime
    source: str  # "finnhub", "polygon", etc.
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None


class FinnhubStreamTask(BackgroundTask):
    """Stream market data from Finnhub API."""
    
    # Symbols to monitor
    SYMBOLS = [
        # Major indices
        "ALPHABETICAL_INDEX",
        "^GSPC",  # S&P 500
        # Top tech stocks
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        # Supply chain related
        "JCI", "FDX", "UPS", "DAL", "AAL",  # Industrial/Transport
        # Commodities
        "CLPR", "USOU", "BCOU",  # Crude oil
    ]
    
    def __init__(self, api_key: str, interval_seconds: int = 30):
        super().__init__(
            name="finnhub_stream",
            interval_seconds=interval_seconds,
            priority=85,  # Very high priority
        )
        self.api_key = api_key
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch stock data from Finnhub."""
        if not self.api_key:
            return {
                "status": "skipped",
                "reason": "Finnhub API key not configured"
            }
        
        cache = await get_cache()
        prices = []
        errors = []
        
        # Fetch in parallel for speed
        tasks = [
            self._fetch_quote(symbol)
            for symbol in self.SYMBOLS
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(self.SYMBOLS, results):
            if isinstance(result, Exception):
                errors.append(f"{symbol}: {str(result)}")
            elif result:
                prices.append(result)
        
        if prices:
            # Cache with 30-second TTL (real-time)
            cache_data = {
                "prices": [p.model_dump() for p in prices],
                "timestamp": datetime.now().isoformat(),
            }
            await cache.setex("stocks:streaming", 30, cache_data)
            
            # Cache individual symbols for fast lookup
            for price in prices:
                key = f"stock:{price.symbol}"
                await cache.setex(key, 30, price.model_dump())
        
        logger.info(f"Finnhub: Fetched prices for {len(prices)} symbols")
        
        return {
            "provider": "finnhub",
            "symbols_fetched": len(prices),
            "errors": errors,
            "cached_at": datetime.now().isoformat(),
        }
    
    async def _fetch_quote(self, symbol: str) -> Optional[StreamAdapter]:
        """Fetch a single stock quote."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"https://finnhub.io/api/v1/quote",
                    params={"symbol": symbol, "token": self.api_key}
                )
                response.raise_for_status()
            
            data = response.json()
            
            if "c" not in data:  # current price
                return None
            
            return StreamAdapter(
                symbol=symbol,
                price=data.get("c", 0),
                change=data.get("d", 0),
                change_percent=data.get("dp", 0),
                bid=data.get("b", None),
                ask=data.get("a", None),
                volume=data.get("v", None),
                timestamp=datetime.now(),
                source="finnhub",
            )
        
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol} from Finnhub: {e}")
            return None


class PolygonStreamTask(BackgroundTask):
    """Stream market data from Polygon.io API."""
    
    SYMBOLS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "JCI", "FDX", "UPS", "DAL", "AAL",
    ]
    
    def __init__(self, api_key: str, interval_seconds: int = 60):
        super().__init__(
            name="polygon_stream",
            interval_seconds=interval_seconds,
            priority=80,
        )
        self.api_key = api_key
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch aggregated market data from Polygon."""
        if not self.api_key:
            return {
                "status": "skipped",
                "reason": "Polygon API key not configured"
            }
        
        cache = await get_cache()
        prices = []
        errors = []
        
        # Fetch all symbols in parallel
        tasks = [
            self._fetch_last_quote(symbol)
            for symbol in self.SYMBOLS
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(self.SYMBOLS, results):
            if isinstance(result, Exception):
                errors.append(f"{symbol}: {str(result)}")
            elif result:
                prices.append(result)
        
        if prices:
            cache_data = {
                "prices": [p.model_dump() for p in prices],
                "timestamp": datetime.now().isoformat(),
            }
            await cache.setex("stocks:polygon", 60, cache_data)
            
            for price in prices:
                key = f"stock:polygon:{price.symbol}"
                await cache.setex(key, 60, price.model_dump())
        
        logger.info(f"Polygon: Fetched prices for {len(prices)} symbols")
        
        return {
            "provider": "polygon",
            "symbols_fetched": len(prices),
            "errors": errors,
            "cached_at": datetime.now().isoformat(),
        }
    
    async def _fetch_last_quote(self, symbol: str) -> Optional[StreamAdapter]:
        """Fetch last quote for a symbol — uses free-tier compatible endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Free tier: use /v2/aggs/ticker/{symbol}/prev (previous close) instead of /v1/last/quote
                # Paid endpoint /v1/last/quote requires Stocks Starter+ and returns 404 on free tier
                response = await client.get(
                    f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev",
                    params={"adjusted": "true", "apikey": self.api_key}
                )
                response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            if not results:
                return None
            
            bar = results[0]  # {o: open, h: high, l: low, c: close, v: volume, t: timestamp}
            
            return StreamAdapter(
                symbol=symbol,
                price=float(bar.get("c", 0)),
                change=float(bar.get("c", 0)) - float(bar.get("o", 0)),
                change_percent=((float(bar.get("c", 0)) - float(bar.get("o", 0))) / float(bar.get("o", 1)) * 100) if bar.get("o") else 0,
                bid=None,
                ask=None,
                volume=int(bar.get("v", 0)) if bar.get("v") else None,
                timestamp=datetime.fromtimestamp(bar.get("t", 0) / 1000),
                source="polygon",
            )
        
        except Exception as e:
            # Downgrade to debug to reduce log noise on free tier rate limits
            logger.debug(f"Failed to fetch {symbol} from Polygon: {e}")
            return None


class ForexStreamTask(BackgroundTask):
    """Stream forex rates from free API."""
    
    PAIRS = [
        "EUR/USD", "GBP/USD", "USD/JPY",
        "USD/CNY", "USD/INR", "USD/CAD",
    ]
    
    def __init__(self, interval_seconds: int = 120):
        super().__init__(
            name="forex_stream",
            interval_seconds=interval_seconds,
            priority=70,
        )
    
    async def execute(self) -> Dict[str, Any]:
        """Fetch forex rates."""
        cache = await get_cache()
        rates = []
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Using exchangerate-api.com (free tier)
                response = await client.get(
                    "https://api.exchangerate-api.com/v4/latest/USD"
                )
                response.raise_for_status()
            
            data = response.json()
            base_rate = data.get("rates", {})
            
            for pair in self.PAIRS:
                from_curr, to_curr = pair.split("/")
                
                if to_curr in base_rate:
                    rate = base_rate[to_curr]
                    rates.append({
                        "pair": pair,
                        "rate": rate,
                        "timestamp": datetime.now().isoformat(),
                    })
            
            # Cache forex rates
            if rates:
                await cache.setex("forex:latest", 120, {
                    "rates": rates,
                    "timestamp": datetime.now().isoformat(),
                })
            
            logger.info(f"Fetched {len(rates)} forex rates")
            return {
                "pairs_fetched": len(rates),
                "cached_at": datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch forex rates: {e}")
            return {
                "error": str(e),
                "pairs_fetched": 0,
            }
