"""
Task System Initialization

Registers and starts all background ingestion tasks.
Strategy #2: Background worker pipeline.
Strategy #3: Vendor streaming APIs.
"""

import logging
import os
from typing import List

from backend.tasks.scheduler import BackgroundTask, get_scheduler

logger = logging.getLogger(__name__)


async def init_all_tasks() -> None:
    """Initialize and start all background tasks."""
    scheduler = get_scheduler()
    
    # Register news ingest task
    try:
        from backend.tasks.ingest_news import NewsIngestTask
        news_task = NewsIngestTask(interval_seconds=300)  # 5 minutes
        scheduler.register_task(news_task)
    except ImportError:
        logger.warning("News ingest task not available")
    
    # Register weather/disaster ingest task
    try:
        from backend.tasks.ingest_weather_disaster import WeatherDisasterIngestTask
        weather_task = WeatherDisasterIngestTask(interval_seconds=600)  # 10 minutes
        scheduler.register_task(weather_task)
    except ImportError:
        logger.warning("Weather/disaster ingest task not available")
    
    # Register commodity ingest task
    try:
        from backend.tasks.ingest_commodities import CommodityIngestTask
        commodity_task = CommodityIngestTask(interval_seconds=300)  # 5 minutes
        scheduler.register_task(commodity_task)
    except ImportError:
        logger.warning("Commodity ingest task not available")
    
    # Register Finnhub streaming task (if API key is available)
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key:
        try:
            from backend.tasks.ingest_market_streams import FinnhubStreamTask
            finnhub_task = FinnhubStreamTask(
                api_key=finnhub_key,
                interval_seconds=30  # 30 seconds for real-time
            )
            scheduler.register_task(finnhub_task)
        except ImportError:
            logger.warning("Finnhub streaming task not available")
    else:
        logger.info("Finnhub streaming disabled (no API key)")
    
    # Register Polygon streaming task (if API key is available)
    polygon_key = os.getenv("POLYGON_API_KEY")
    if polygon_key:
        try:
            from backend.tasks.ingest_market_streams import PolygonStreamTask
            polygon_task = PolygonStreamTask(
                api_key=polygon_key,
                interval_seconds=60
            )
            scheduler.register_task(polygon_task)
        except ImportError:
            logger.warning("Polygon streaming task not available")
    else:
        logger.info("Polygon streaming disabled (no API key)")
    
    # Register forex streaming task
    try:
        from backend.tasks.ingest_market_streams import ForexStreamTask
        forex_task = ForexStreamTask(interval_seconds=120)  # 2 minutes
        scheduler.register_task(forex_task)
    except ImportError:
        logger.warning("Forex streaming task not available")
    
    logger.info(f"Registered {len(scheduler.tasks)} background tasks")


async def start_scheduler() -> None:
    """Start the background task scheduler."""
    await init_all_tasks()
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler() -> None:
    """Stop the background task scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
