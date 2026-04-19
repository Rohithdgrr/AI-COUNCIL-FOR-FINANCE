"""
Webhook Management API Routes

Endpoints for managing webhook subscriptions.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel, HttpUrl
import logging

from backend.api.webhooks import (
    webhook_manager,
    WebhookSubscription,
    SUPPORTED_EVENTS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SubscribeRequest(BaseModel):
    """Request to subscribe to webhook events."""
    url: HttpUrl
    events: List[str]


class SubscribeResponse(BaseModel):
    """Response after subscribing."""
    subscription_id: str
    secret: str
    message: str


class UnsubscribeResponse(BaseModel):
    """Response after unsubscribing."""
    success: bool
    message: str


class WebhookSubscriptionResponse(BaseModel):
    """Webhook subscription details."""
    id: str
    url: str
    events: List[str]
    active: bool
    created_at: str
    last_triggered: str | None
    total_deliveries: int
    failed_deliveries: int


class SupportedEventsResponse(BaseModel):
    """List of supported webhook events."""
    events: List[str]
    count: int


# ============================================================================
# Routes
# ============================================================================

@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(request: SubscribeRequest):
    """
    Subscribe to webhook events.
    
    Returns subscription ID and secret for HMAC verification.
    """
    try:
        subscription = WebhookSubscription(
            url=request.url,
            events=request.events,
        )
        
        subscription_id = await webhook_manager.subscribe(subscription)
        
        # Get the created subscription to return the secret
        created_sub = webhook_manager.subscriptions[subscription_id]
        
        return SubscribeResponse(
            subscription_id=subscription_id,
            secret=created_sub.secret,
            message=f"Successfully subscribed to {len(request.events)} events",
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Failed to create webhook subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.delete("/subscribe/{subscription_id}", response_model=UnsubscribeResponse)
async def unsubscribe(subscription_id: str):
    """
    Unsubscribe from webhook events.
    """
    try:
        success = await webhook_manager.unsubscribe(subscription_id)
        
        if success:
            return UnsubscribeResponse(
                success=True,
                message=f"Successfully unsubscribed {subscription_id}",
            )
        else:
            raise HTTPException(status_code=404, detail="Subscription not found")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to delete webhook subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete subscription")


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions():
    """
    List all active webhook subscriptions.
    """
    try:
        subscriptions = await webhook_manager.list_subscriptions()
        
        return [
            WebhookSubscriptionResponse(
                id=sub.id,
                url=str(sub.url),
                events=sub.events,
                active=sub.active,
                created_at=sub.created_at.isoformat() if sub.created_at else "",
                last_triggered=sub.last_triggered.isoformat() if sub.last_triggered else None,
                total_deliveries=sub.total_deliveries,
                failed_deliveries=sub.failed_deliveries,
            )
            for sub in subscriptions
        ]
    
    except Exception as e:
        logger.error(f"Failed to list webhook subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list subscriptions")


@router.get("/events", response_model=SupportedEventsResponse)
async def list_supported_events():
    """
    List all supported webhook events.
    """
    return SupportedEventsResponse(
        events=SUPPORTED_EVENTS,
        count=len(SUPPORTED_EVENTS),
    )


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_subscription(subscription_id: str):
    """
    Get details of a specific webhook subscription.
    """
    try:
        subscription = webhook_manager.subscriptions.get(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return WebhookSubscriptionResponse(
            id=subscription.id,
            url=str(subscription.url),
            events=subscription.events,
            active=subscription.active,
            created_at=subscription.created_at.isoformat() if subscription.created_at else "",
            last_triggered=subscription.last_triggered.isoformat() if subscription.last_triggered else None,
            total_deliveries=subscription.total_deliveries,
            failed_deliveries=subscription.failed_deliveries,
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to get webhook subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")
