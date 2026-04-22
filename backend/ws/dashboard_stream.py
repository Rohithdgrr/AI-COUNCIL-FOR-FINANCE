import asyncio
import logging
from datetime import datetime

from backend.routes.market import get_commodity_prices, get_global_news, get_risk_dashboard, get_supply_chain_stocks
from backend.ws.events import EventType, Topic, emit_event

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 60


async def build_dashboard_snapshot() -> dict:
    tasks = [
        asyncio.wait_for(get_risk_dashboard(), timeout=20),
        asyncio.wait_for(get_commodity_prices(), timeout=20),
        asyncio.wait_for(get_global_news(), timeout=20),
        asyncio.wait_for(get_supply_chain_stocks(), timeout=20),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    def unwrap(result: object, fallback: dict) -> dict:
        return result if isinstance(result, dict) else fallback

    return {
        "risk_dashboard": unwrap(results[0], {"regions": [], "global_disasters": {"alerts": []}}),
        "commodity_prices": unwrap(results[1], {"commodities": []}),
        "global_news": unwrap(results[2], {"news": []}),
        "supply_chain_stocks": unwrap(results[3], {"stocks": []}),
        "timestamp": datetime.now().isoformat(),
        "source": "market-stream",
    }


async def run_dashboard_stream(interval_seconds: int = DEFAULT_INTERVAL_SECONDS):
    logger.info("Starting dashboard websocket stream", extra={"interval_seconds": interval_seconds})

    while True:
        try:
            snapshot = await build_dashboard_snapshot()
            await emit_event(EventType.DASHBOARD_SNAPSHOT, snapshot, topic=Topic.DASHBOARD)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(f"Dashboard snapshot broadcast failed: {exc}")

        await asyncio.sleep(interval_seconds)