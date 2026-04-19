"""
Webhook Event System for SupplyChainGPT

Features:
- Real-time event notifications
- HMAC signature verification
- Automatic retry with exponential backoff
- Event filtering and subscriptions
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================

class WebhookSubscription(BaseModel):
    """Webhook subscription configuration."""
    id: Optional[str] = None
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    total_deliveries: int = 0
    failed_deliveries: int = 0


class WebhookEvent(BaseModel):
    """Webhook event payload."""
    event: str
    timestamp: datetime
    payload: Dict[str, Any]
    subscription_id: str


# ============================================================================
# Supported Events
# ============================================================================

SUPPORTED_EVENTS = [
    "agent.completed",              # Agent finished analysis
    "debate.started",               # Council debate started
    "debate.consensus_reached",     # Council reached agreement
    "debate.completed",             # Debate finished
    "risk.alert",                   # High risk detected
    "supplier.status_change",       # Supplier health changed
    "shipment.delayed",             # Shipment delay detected
    "shipment.arrived",             # Shipment arrived
    "price.threshold_breach",       # Price crossed threshold
    "esg.compliance_issue",         # ESG violation detected
    "financial.credit_downgrade",   # Supplier credit downgraded
    "system.health_degraded",       # System health issue
]


# ============================================================================
# Webhook Manager
# ============================================================================

class WebhookManager:
    """Manage webhook subscriptions and delivery."""
    
    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # seconds
    
    async def subscribe(self, subscription: WebhookSubscription) -> str:
        """Subscribe to webhook events."""
        # Generate ID and secret
        subscription.id = secrets.token_urlsafe(16)
        subscription.secret = secrets.token_urlsafe(32)
        subscription.created_at = datetime.now()
        
        # Validate events
        invalid_events = [e for e in subscription.events if e not in SUPPORTED_EVENTS]
        if invalid_events:
            raise ValueError(f"Invalid events: {invalid_events}")
        
        # Store subscription
        self.subscriptions[subscription.id] = subscription
        
        # Persist to database
        await self._persist_subscription(subscription)
        
        logger.info(f"Created webhook subscription {subscription.id} for {subscription.url}")
        
        return subscription.id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from webhook events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            
            # Remove from database
            await self._delete_subscription(subscription_id)
            
            logger.info(f"Deleted webhook subscription {subscription_id}")
            return True
        
        return False
    
    async def list_subscriptions(self) -> List[WebhookSubscription]:
        """List all active subscriptions."""
        return list(self.subscriptions.values())
    
    async def notify(self, event: str, payload: Dict[str, Any]):
        """Send webhook notifications for an event."""
        if event not in SUPPORTED_EVENTS:
            logger.warning(f"Unknown event type: {event}")
            return
        
        # Find matching subscriptions
        matching = [
            sub for sub in self.subscriptions.values()
            if sub.active and event in sub.events
        ]
        
        if not matching:
            logger.debug(f"No subscribers for event: {event}")
            return
        
        logger.info(f"Notifying {len(matching)} subscribers for event: {event}")
        
        # Queue deliveries
        for subscription in matching:
            webhook_event = WebhookEvent(
                event=event,
                timestamp=datetime.now(),
                payload=payload,
                subscription_id=subscription.id,
            )
            
            await self.delivery_queue.put((subscription, webhook_event))
    
    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent,
    ):
        """Deliver webhook with retry logic."""
        # Prepare payload
        payload_json = json.dumps({
            "event": event.event,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload,
        })
        
        # Generate HMAC signature
        signature = hmac.new(
            subscription.secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event.event,
            "X-Webhook-Timestamp": event.timestamp.isoformat(),
            "X-Webhook-ID": event.subscription_id,
        }
        
        # Retry loop
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        str(subscription.url),
                        content=payload_json,
                        headers=headers,
                    )
                    
                    if response.status_code < 300:
                        # Success
                        subscription.last_triggered = datetime.now()
                        subscription.total_deliveries += 1
                        
                        logger.info(
                            f"Webhook delivered to {subscription.url} "
                            f"for event {event.event}"
                        )
                        
                        await self._update_subscription_stats(subscription)
                        return
                    else:
                        logger.warning(
                            f"Webhook delivery failed with status {response.status_code} "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
            
            except Exception as e:
                logger.warning(
                    f"Webhook delivery error: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
            
            # Retry delay
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delays[attempt])
        
        # All retries failed
        subscription.failed_deliveries += 1
        await self._update_subscription_stats(subscription)
        
        logger.error(
            f"Webhook delivery failed after {self.max_retries} attempts "
            f"to {subscription.url} for event {event.event}"
        )
    
    async def start_delivery_worker(self):
        """Start background worker for webhook delivery."""
        logger.info("Starting webhook delivery worker")
        
        while True:
            try:
                subscription, event = await self.delivery_queue.get()
                
                # Deliver in background
                asyncio.create_task(self._deliver_webhook(subscription, event))
                
            except Exception as e:
                logger.error(f"Webhook delivery worker error: {e}")
                await asyncio.sleep(1)
    
    async def _persist_subscription(self, subscription: WebhookSubscription):
        """Persist subscription to database."""
        try:
            from backend.db.neon import get_pool
            
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO webhook_subscriptions 
                    (id, url, events, secret, active, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    subscription.id,
                    str(subscription.url),
                    subscription.events,
                    subscription.secret,
                    subscription.active,
                    subscription.created_at,
                )
        except Exception as e:
            logger.error(f"Failed to persist subscription: {e}")
    
    async def _delete_subscription(self, subscription_id: str):
        """Delete subscription from database."""
        try:
            from backend.db.neon import get_pool
            
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM webhook_subscriptions WHERE id = $1",
                    subscription_id,
                )
        except Exception as e:
            logger.error(f"Failed to delete subscription: {e}")
    
    async def _update_subscription_stats(self, subscription: WebhookSubscription):
        """Update subscription statistics."""
        try:
            from backend.db.neon import get_pool
            
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE webhook_subscriptions 
                    SET last_triggered = $1, 
                        total_deliveries = $2,
                        failed_deliveries = $3
                    WHERE id = $4
                    """,
                    subscription.last_triggered,
                    subscription.total_deliveries,
                    subscription.failed_deliveries,
                    subscription.id,
                )
        except Exception as e:
            logger.error(f"Failed to update subscription stats: {e}")
    
    async def load_subscriptions(self):
        """Load subscriptions from database on startup."""
        try:
            from backend.db.neon import get_pool
            
            pool = await get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM webhook_subscriptions WHERE active = true"
                )
                
                for row in rows:
                    subscription = WebhookSubscription(
                        id=row["id"],
                        url=row["url"],
                        events=row["events"],
                        secret=row["secret"],
                        active=row["active"],
                        created_at=row["created_at"],
                        last_triggered=row.get("last_triggered"),
                        total_deliveries=row.get("total_deliveries", 0),
                        failed_deliveries=row.get("failed_deliveries", 0),
                    )
                    
                    self.subscriptions[subscription.id] = subscription
                
                logger.info(f"Loaded {len(self.subscriptions)} webhook subscriptions")
        
        except Exception as e:
            logger.warning(f"Failed to load subscriptions: {e}")


# ============================================================================
# Global Instance
# ============================================================================

webhook_manager = WebhookManager()


# ============================================================================
# Convenience Functions
# ============================================================================

async def notify_event(event: str, payload: Dict[str, Any]):
    """Send webhook notification for an event."""
    await webhook_manager.notify(event, payload)


async def subscribe_webhook(url: str, events: List[str]) -> str:
    """Subscribe to webhook events."""
    subscription = WebhookSubscription(url=url, events=events)
    return await webhook_manager.subscribe(subscription)


async def unsubscribe_webhook(subscription_id: str) -> bool:
    """Unsubscribe from webhook events."""
    return await webhook_manager.unsubscribe(subscription_id)


# Example usage:
"""
from backend.api.webhooks import notify_event, subscribe_webhook

# Subscribe to events
subscription_id = await subscribe_webhook(
    url="https://example.com/webhooks",
    events=["debate.completed", "risk.alert"]
)

# Send notification
await notify_event("debate.completed", {
    "debate_id": "abc123",
    "query": "Assess supplier risk",
    "consensus_reached": True,
    "final_confidence": 0.85
})
"""
