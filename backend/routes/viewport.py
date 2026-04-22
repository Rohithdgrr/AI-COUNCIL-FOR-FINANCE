"""
Viewport Management API Endpoints

Handle WebSocket subscriptions based on dashboard visibility.
Strategy #10: Stream only visible panels.
"""

from fastapi import APIRouter, WebSocket, Query, HTTPException
from typing import List
import logging

from backend.viewport.viewport_streaming import (
    get_viewport_manager,
    get_frontend_config,
    cleanup_session,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/viewport", tags=["Viewport"])


@router.get("/config")
async def get_viewport_config():
    """Get frontend viewport tracking configuration."""
    return get_frontend_config()


@router.post("/update-visibility")
async def update_panel_visibility(
    session_id: str = Query(...),
    panels: List[str] = Query(...),
) -> dict:
    """
    Update which dashboard panels are currently visible.
    
    Call this when user scrolls or viewport changes.
    """
    manager = get_viewport_manager(session_id)
    
    try:
        result = await manager.on_viewport_change(panels)
        return result
    except Exception as e:
        logger.error(f"Failed to update viewport for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/{session_id}")
async def cleanup_viewport_session(session_id: str) -> dict:
    """Clean up viewport manager for session."""
    cleanup_session(session_id)
    return {"message": f"Cleaned up session {session_id}"}


@router.get("/status/{session_id}")
async def get_viewport_status(session_id: str) -> dict:
    """Get current viewport status for session."""
    manager = get_viewport_manager(session_id)
    
    return {
        "session_id": session_id,
        "visible_panels": list(manager.subscribed_topics),
        "active_subscriptions": list(manager.subscribed_topics),
        "panel_count": len(manager.subscribed_topics),
    }
