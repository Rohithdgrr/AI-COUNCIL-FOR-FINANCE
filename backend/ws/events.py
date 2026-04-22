import enum
import time
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EventType(str, enum.Enum):
    COUNCIL_TOKEN = "council_token"
    COUNCIL_COMPLETE = "council_complete"
    COUNCIL_AGENT_START = "council_agent_start"
    COUNCIL_AGENT_DONE = "council_agent_done"
    COUNCIL_AGENT_ERROR = "council_agent_error"
    RISK_ALERT = "risk_alert"
    DASHBOARD_SNAPSHOT = "dashboard_snapshot"
    RAG_INDEXED = "rag_indexed"
    MCP_TOOL_RESULT = "mcp_tool_result"
    SETTINGS_UPDATED = "settings_updated"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class Topic(str, enum.Enum):
    COUNCIL = "council"
    RISK = "risk"
    DASHBOARD = "dashboard"
    RAG = "rag"
    MCP = "mcp"
    SETTINGS = "settings"


def build_event(
    event_type: EventType,
    payload: Any = None,
    session_id: Optional[str] = None,
) -> dict:
    return {
        "type": event_type.value,
        "session_id": session_id,
        "payload": payload,
        "timestamp": time.time(),
    }


async def emit_event(event_type: EventType, payload: Any = None, session_id: Optional[str] = None, topic: Optional[Topic] = None):
    from backend.ws.server import manager
    event = build_event(event_type, payload, session_id)
    if topic:
        await manager.broadcast_to_topic(topic.value, event)
    else:
        await manager.broadcast(event)
    logger.debug(f"Emitted event: {event_type.value} topic={topic}")


async def subscribe_topic(websocket, topic: Topic):
    from backend.ws.server import manager
    manager.subscribe(websocket, topic.value)
    await manager.send_to(websocket, build_event(EventType.HEARTBEAT, {"status": "subscribed", "topic": topic.value}))

    if topic == Topic.DASHBOARD:
        try:
            from backend.ws.dashboard_stream import build_dashboard_snapshot

            snapshot = await build_dashboard_snapshot()
            await manager.send_to(websocket, build_event(EventType.DASHBOARD_SNAPSHOT, snapshot, session_id="dashboard-init"))
        except Exception as exc:
            logger.warning(f"Initial dashboard snapshot failed: {exc}")


async def unsubscribe_topic(websocket, topic: Topic):
    from backend.ws.server import manager
    manager.unsubscribe(websocket, topic.value)
