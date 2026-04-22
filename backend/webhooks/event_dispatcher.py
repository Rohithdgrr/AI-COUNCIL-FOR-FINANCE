"""
Webhook Event Triggers for Background Tasks

Fire webhooks when data ingestion tasks complete or detect critical events.
Enables external systems to react to supply chain alerts in real-time.
Strategy #4: Use webhooks for event-driven sources.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook event types."""
    # Task events
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Data events
    NEWS_ALERT = "news.alert"
    PRICE_THRESHOLD_BREACH = "price.threshold_breach"
    WEATHER_ALERT = "weather.alert"
    EARTHQUAKE_DETECTED = "earthquake.detected"
    SUPPLY_CHAIN_RISK = "supply_chain.risk"


class WebhookEventDispatcher:
    """Dispatch webhook events from background tasks."""
    
    def __init__(self, webhook_manager=None):
        self.webhook_manager = webhook_manager
    
    async def dispatch_task_completion(
        self,
        task_name: str,
        result: Dict[str, Any],
        success: bool,
    ) -> None:
        """Dispatch webhook when task completes."""
        if not self.webhook_manager:
            return
        
        event_type = "task.completed" if success else "task.failed"
        
        await self.webhook_manager.notify(
            event=event_type,
            payload={
                "task_name": task_name,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "status": "success" if success else "failed",
            },
        )
        
        logger.debug(f"Dispatched webhook for {event_type}: {task_name}")
    
    async def dispatch_price_alert(
        self,
        symbol: str,
        price: float,
        threshold: float,
        direction: str,  # "above" or "below"
    ) -> None:
        """Dispatch alert when commodity price breaches threshold."""
        if not self.webhook_manager:
            return
        
        await self.webhook_manager.notify(
            event=WebhookEventType.PRICE_THRESHOLD_BREACH,
            payload={
                "symbol": symbol,
                "price": price,
                "threshold": threshold,
                "direction": direction,
                "timestamp": datetime.now().isoformat(),
            },
        )
        
        logger.info(f"Price alert for {symbol}: ${price} ({direction} ${threshold})")
    
    async def dispatch_weather_alert(
        self,
        location: str,
        alert_level: str,
        condition: str,
        temperature: float,
    ) -> None:
        """Dispatch alert for severe weather."""
        if not self.webhook_manager or alert_level == "normal":
            return
        
        await self.webhook_manager.notify(
            event=WebhookEventType.WEATHER_ALERT,
            payload={
                "location": location,
                "alert_level": alert_level,
                "condition": condition,
                "temperature": temperature,
                "timestamp": datetime.now().isoformat(),
            },
        )
        
        logger.info(f"Weather alert at {location}: {alert_level} - {condition}")
    
    async def dispatch_earthquake_alert(
        self,
        location: str,
        magnitude: float,
        latitude: float,
        longitude: float,
        depth_km: float,
    ) -> None:
        """Dispatch alert for significant earthquake."""
        if not self.webhook_manager or magnitude < 4.5:  # Only significant quakes
            return
        
        await self.webhook_manager.notify(
            event=WebhookEventType.EARTHQUAKE_DETECTED,
            payload={
                "location": location,
                "magnitude": magnitude,
                "latitude": latitude,
                "longitude": longitude,
                "depth_km": depth_km,
                "timestamp": datetime.now().isoformat(),
            },
        )
        
        logger.warning(f"Earthquake alert: {location} Magnitude {magnitude}")
    
    async def dispatch_risk_alert(
        self,
        supplier_id: str,
        risk_level: str,
        reason: str,
        affected_shipments: int,
    ) -> None:
        """Dispatch alert for supply chain risk."""
        if not self.webhook_manager or risk_level == "low":
            return
        
        await self.webhook_manager.notify(
            event=WebhookEventType.SUPPLY_CHAIN_RISK,
            payload={
                "supplier_id": supplier_id,
                "risk_level": risk_level,
                "reason": reason,
                "affected_shipments": affected_shipments,
                "timestamp": datetime.now().isoformat(),
            },
        )
        
        logger.warning(f"Supply chain risk: {supplier_id} ({risk_level})")


# Global dispatcher instance
_dispatcher_instance: Optional[WebhookEventDispatcher] = None


def get_webhook_dispatcher() -> WebhookEventDispatcher:
    """Get or create global webhook dispatcher."""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = WebhookEventDispatcher()
    return _dispatcher_instance


async def init_webhook_dispatcher(webhook_manager) -> WebhookEventDispatcher:
    """Initialize webhook dispatcher with manager."""
    global _dispatcher_instance
    _dispatcher_instance = WebhookEventDispatcher(webhook_manager)
    logger.info("Webhook event dispatcher initialized")
    return _dispatcher_instance
