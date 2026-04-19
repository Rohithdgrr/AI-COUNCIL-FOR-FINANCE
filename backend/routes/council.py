from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
from backend.graph import build_council_graph, run_council_streaming
from backend.llm.router import llm_router
from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
from backend.agents.supply_agent import SYSTEM_PROMPT as SUPPLY_PROMPT
from backend.agents.logistics_agent import SYSTEM_PROMPT as LOGISTICS_PROMPT
from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
from backend.agents.finance_agent import SYSTEM_PROMPT as FINANCE_PROMPT
from backend.agents.brand_agent import SYSTEM_PROMPT as BRAND_PROMPT
from backend.agents.moderator import SYSTEM_PROMPT as MODERATOR_PROMPT
from backend.ws.events import EventType, Topic, emit_event
from backend.observability.langsmith_config import (
    CouncilTracer, record_agent_call, record_debate_round, record_mcp_call,
)
from backend.middleware.security import sanitize_input, redact_pii
from backend.config import settings


_council_compiled: Optional[any] = None


def _get_council_compiled():
    global _council_compiled
    if _council_compiled is None:
        graph = build_council_graph()
        compile_kwargs = {}
        if settings.human_in_loop:
            compile_kwargs["interrupt_before"] = ["synthesize"]
        _council_compiled = graph.compile(**compile_kwargs)
    return _council_compiled
import uuid
import time
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

AGENT_PROMPTS = {
    "risk": RISK_PROMPT,
    "supply": SUPPLY_PROMPT,
    "logistics": LOGISTICS_PROMPT,
    "market": MARKET_PROMPT,
    "finance": FINANCE_PROMPT,
    "brand": BRAND_PROMPT,
}


class CouncilRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    ws_session_id: Optional[str] = None


class CouncilQueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    stream: Optional[bool] = False
    lite: Optional[bool] = None  # Skip Round 2 for faster verdict; None = use config default
    enable_self_critique: Optional[bool] = None  # Enable self-critique round; None = use config default


class FallbackExecuteRequest(BaseModel):
    session_id: str
    fallback_index: int = 0  # index into tiered_fallbacks list


class CouncilResponse(BaseModel):
    session_id: str
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    agent_outputs: list = []
    evidence: list = []
    round_number: int = 0
    status: str = "pending"
    latency_ms: int = 0
    astra_results: Optional[dict] = None  # ⭐ Astra simulation results


# ---------------------------------------------------------------------------
# Day 6: POST /council/query — full graph with debate + optional streaming
# ---------------------------------------------------------------------------
@router.post("/query")
async def council_query(request: CouncilQueryRequest):
    """Run the full council graph with debate engine, predictions, and fallbacks.

    If stream=True, returns SSE with intermediate results.
    Otherwise returns the complete result as JSON.
    """
    query = sanitize_input(request.query)

    # Build debate_config from per-request overrides
    debate_config = {}
    if request.lite is not None:
        debate_config["lite"] = request.lite
    if request.enable_self_critique is not None:
        debate_config["enable_self_critique"] = request.enable_self_critique

    # Merge debate_config into context
    ctx = request.context or {}
    if debate_config:
        ctx["debate_config"] = debate_config

    if request.stream:
        return await _council_query_stream(query, ctx)

    session_id = str(uuid.uuid4())
    start = time.time()
    tracer = CouncilTracer(session_id)

    try:
        # Check query-based cache for identical queries within TTL
        import hashlib
        cache_key = f"council_cache:{hashlib.sha256(query.encode()).hexdigest()}"
        if debate_config:
            cache_key += f":{hashlib.sha256(json.dumps(debate_config, sort_keys=True).encode()).hexdigest()[:8]}"
        try:
            from backend.db.redis_client import cache_get
            cached = await cache_get(cache_key)
            if cached:
                logger.info(f"Cache hit for query: {query[:60]}...")
                cached["cached"] = True
                return CouncilResponse(
                    session_id=cached.get("session_id", session_id),
                    recommendation=cached.get("recommendation"),
                    confidence=cached.get("confidence"),
                    agent_outputs=cached.get("agent_outputs", []),
                    evidence=[],
                    round_number=cached.get("round_number", 0),
                    status="complete",
                    latency_ms=0,
                )
        except Exception:
            pass  # Cache unavailable — proceed normally

        compiled = _get_council_compiled()

        initial_state = {
            "query": query,
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": session_id,
            "context": ctx,
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "astra_results": None,  # ⭐ Astra integration
        }

        result = await compiled.ainvoke(initial_state)
        latency_ms = int((time.time() - start) * 1000)

        # Record metrics
        record_debate_round(
            session_id=session_id,
            round_number=result.get("round_number", 0),
            phase="complete",
            confidence=result.get("confidence", 0) * 100,
            risk_score=result.get("risk_score", 0),
            latency_ms=latency_ms,
        )

        # Store session to Redis
        try:
            from backend.db.redis_client import cache_set
            from backend.config import settings as _s
            session_data = {
                "session_id": session_id,
                "query": query,
                "recommendation": result.get("recommendation", ""),
                "confidence": result.get("confidence", 0),
                "risk_score": result.get("risk_score", 0),
                "debate_rounds": result.get("debate_rounds", []),
                "agent_outputs": [
                    {"agent": o.agent, "confidence": o.confidence, "contribution": o.contribution[:300]}
                    for o in result.get("agent_outputs", [])
                ],
                "tiered_fallbacks": result.get("tiered_fallbacks", []),
                "predictions": result.get("predictions", []),
                "astra_results": result.get("astra_results"),  # ⭐ Include Astra results
                "timestamp": time.time(),
            }
            await cache_set(f"council_session:{session_id}", session_data, ttl=_s.session_store_ttl)
        except Exception as e:
            logger.warning(f"Session storage failed: {e}")

        # Store in query-based cache for duplicate query avoidance
        try:
            from backend.db.redis_client import cache_set as _cache_set
            from backend.config import settings as _s
            cache_data = {
                "session_id": session_id,
                "recommendation": result.get("recommendation", ""),
                "confidence": result.get("confidence", 0),
                "risk_score": result.get("risk_score", 0),
                "agent_outputs": [
                    {"agent": o.agent, "confidence": o.confidence, "contribution": o.contribution[:300]}
                    for o in result.get("agent_outputs", [])
                ],
                "round_number": result.get("round_number", 0),
                "tiered_fallbacks": result.get("tiered_fallbacks", []),
                "predictions": result.get("predictions", []),
            }
            await _cache_set(cache_key, cache_data, ttl=_s.council_cache_ttl)
        except Exception:
            pass  # Cache write failure is non-critical

        trace_url = tracer.get_trace_url()

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "recommendation": result.get("recommendation"),
                "confidence": result.get("confidence"),
                "risk_score": result.get("risk_score"),
                "agent_outputs": [o.model_dump() for o in result.get("agent_outputs", [])],
                "evidence": [e.model_dump() for e in result.get("evidence", [])],
                "debate_rounds": result.get("debate_rounds", []),
                "predictions": result.get("predictions", []),
                "tiered_fallbacks": result.get("tiered_fallbacks", []),
                "brand_sentiment": result.get("brand_sentiment"),
                "astra_results": result.get("astra_results"),  # ⭐ Include Astra results
                "round_number": result.get("round_number", 0),
                "latency_ms": latency_ms,
                "trace_url": trace_url,
            },
            "error": None,
        }
    except Exception as e:
        logger.error(f"Council query failed: {e}", extra={"session_id": session_id})
        return {
            "success": False,
            "data": None,
            "error": f"Council analysis failed: {e}",
        }


async def _council_query_stream(query: str, context: dict | None = None):
    """SSE streaming variant of /council/query."""
    session_id = str(uuid.uuid4())

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

        async for payload in run_council_streaming(
            query=query,
            context=context,
            session_id=session_id,
        ):
            yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Day 6: GET /council/history — past sessions from Redis
# ---------------------------------------------------------------------------
@router.get("/history")
async def council_history(limit: int = 20, offset: int = 0):
    """Return past council sessions stored in Redis."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        keys = await r.keys("council_session:*")
        # Sort by timestamp (most recent first)
        sessions = []
        for key in keys[offset: offset + limit]:
            data = await r.get(key)
            if data:
                import json as _json
                sessions.append(_json.loads(data))
        sessions.sort(key=lambda s: s.get("timestamp", 0), reverse=True)

        return {
            "success": True,
            "data": {
                "sessions": sessions,
                "total": len(keys),
                "limit": limit,
                "offset": offset,
            },
            "error": None,
        }
    except Exception as e:
        logger.warning(f"Council history unavailable (Redis may be down): {e}")
        return {
            "success": False,
            "data": {"sessions": [], "total": 0},
            "error": f"Session history unavailable: {e}",
        }


# ---------------------------------------------------------------------------
# GET /council/session/{session_id} — retrieve a specific session
# ---------------------------------------------------------------------------
@router.get("/session/{session_id}")
async def council_session(session_id: str):
    """Return a specific council session by ID from Redis."""
    try:
        from backend.db.redis_client import get_redis
        r = await get_redis()
        data = await r.get(f"council_session:{session_id}")
        if not data:
            raise HTTPException(404, f"Session '{session_id}' not found")
        import json as _json
        session = _json.loads(data)
        return {"success": True, "data": session, "error": None}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Council session lookup failed: {e}")
        return {"success": False, "data": None, "error": f"Session lookup failed: {e}"}


# ---------------------------------------------------------------------------
# GET/PUT /council/config — modular debate configuration at runtime
# ---------------------------------------------------------------------------
class CouncilConfigRequest(BaseModel):
    max_debate_rounds: Optional[int] = None
    confidence_gap_threshold: Optional[float] = None
    council_lite_mode: Optional[bool] = None
    enable_self_critique: Optional[bool] = None
    human_in_loop: Optional[bool] = None
    council_cache_ttl: Optional[int] = None


@router.get("/config")
async def get_council_config():
    """Return current council/debate configuration from settings."""
    return {
        "success": True,
        "data": {
            "max_debate_rounds": settings.max_debate_rounds,
            "confidence_gap_threshold": settings.confidence_gap_threshold,
            "council_lite_mode": settings.council_lite_mode,
            "enable_self_critique": settings.enable_self_critique,
            "human_in_loop": settings.human_in_loop,
            "council_cache_ttl": settings.council_cache_ttl,
        },
        "error": None,
    }


@router.put("/config")
async def update_council_config(request: CouncilConfigRequest):
    """Update council/debate configuration at runtime (in-memory only, not persisted).

    This allows toggling lite mode, self-critique, human-in-loop, etc.
    without restarting the server.
    """
    updates = request.model_dump(exclude_none=True)
    if not updates:
        return {"success": False, "data": None, "error": "No configuration values provided"}

    applied = {}
    for key, value in updates.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
            applied[key] = value
        else:
            logger.warning(f"Unknown config key: {key}")

    logger.info(f"Council config updated: {applied}")

    # Re-initialize debate engine singleton with new settings
    try:
        from backend.debate_engine import DebateEngine
        import backend.debate_engine as de_mod
        de_mod.debate_engine = DebateEngine(
            max_rounds=settings.max_debate_rounds,
            consensus_threshold=settings.confidence_gap_threshold,
            lite_mode=settings.council_lite_mode,
            enable_self_critique=settings.enable_self_critique,
        )
    except Exception as e:
        logger.warning(f"Debate engine re-init after config update failed: {e}")

    return {
        "success": True,
        "data": {"updated": applied},
        "error": None,
    }


# ---------------------------------------------------------------------------
# Day 6: POST /council/execute-fallback — one-click fallback via MCP
# ---------------------------------------------------------------------------
@router.post("/execute-fallback")
async def execute_fallback(request: FallbackExecuteRequest):
    """Execute a fallback option via its linked MCP tool.

    Loads the session from Redis, picks the fallback at the given index,
    and invokes the MCP tool specified in the fallback.
    """
    try:
        from backend.db.redis_client import cache_get
        session = await cache_get(f"council_session:{request.session_id}")
    except Exception as e:
        return {"success": False, "data": None, "error": f"Could not load session: {e}"}

    if not session:
        return {"success": False, "data": None, "error": f"Session {request.session_id} not found"}

    fallbacks = session.get("tiered_fallbacks", [])
    if request.fallback_index >= len(fallbacks):
        return {
            "success": False,
            "data": None,
            "error": f"Fallback index {request.fallback_index} out of range (0-{len(fallbacks)-1})",
        }

    fallback = fallbacks[request.fallback_index]
    mcp_tool = fallback.get("mcp_tool")
    mcp_params = fallback.get("mcp_params", {})

    if not mcp_tool:
        return {
            "success": False,
            "data": None,
            "error": f"Fallback '{fallback.get('name')}' has no linked MCP tool for auto-execution. Manual execution required.",
        }

    # Invoke the MCP tool
    start = time.time()
    try:
        from backend.mcp.mcp_toolkit import get_scoped_client
        client = get_scoped_client("moderator")
        result = await client.call_tool(mcp_tool, mcp_params)
        latency_ms = int((time.time() - start) * 1000)

        record_mcp_call(
            tool_name=mcp_tool, agent="moderator",
            latency_ms=latency_ms, success=True,
        )

        return {
            "success": True,
            "data": {
                "session_id": request.session_id,
                "fallback_name": fallback.get("name"),
                "fallback_tier": fallback.get("tier"),
                "mcp_tool": mcp_tool,
                "mcp_result": result,
                "latency_ms": latency_ms,
            },
            "error": None,
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        record_mcp_call(
            tool_name=mcp_tool or "unknown", agent="moderator",
            latency_ms=latency_ms, success=False,
        )
        return {
            "success": False,
            "data": None,
            "error": f"MCP tool '{mcp_tool}' execution failed: {e}",
        }


# ---------------------------------------------------------------------------
# Original endpoints (kept for backward compatibility)
# ---------------------------------------------------------------------------
@router.post("/analyze", response_model=CouncilResponse)
async def council_analyze(request: CouncilRequest):
    session_id = str(uuid.uuid4())
    start = time.time()

    try:
        compiled = _get_council_compiled()

        initial_state = {
            "query": request.query,
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": session_id,
            "context": request.context,
        }

        result = await compiled.ainvoke(initial_state)

        latency_ms = int((time.time() - start) * 1000)

        return CouncilResponse(
            session_id=session_id,
            recommendation=result.get("recommendation"),
            confidence=result.get("confidence"),
            agent_outputs=[o.model_dump() for o in result.get("agent_outputs", [])],
            evidence=[e.model_dump() for e in result.get("evidence", [])],
            round_number=result.get("round_number", 0),
            status=result.get("status", "complete"),
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error(f"Council analysis failed: {e}")
        raise HTTPException(500, f"Council analysis failed: {e}")


@router.post("/stream")
async def council_stream(request: CouncilRequest):
    """SSE streaming endpoint — streams each agent's output token by token."""
    session_id = str(uuid.uuid4())

    ws_sid = request.ws_session_id

    async def event_generator():
        # Send session start
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        await emit_event(EventType.COUNCIL_TOKEN, {"type": "start", "session_id": session_id}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Stream each agent in sequence
        agent_outputs = {}
        for agent_name, system_prompt in AGENT_PROMPTS.items():
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': agent_name})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_START, {"agent": agent_name}, session_id=ws_sid, topic=Topic.COUNCIL)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze for: {request.query}"},
            ]

            full_response = ""
            try:
                async for token in llm_router.stream_with_fallback(agent_name, messages):
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'agent': agent_name, 'content': token})}\n\n"
                    await emit_event(EventType.COUNCIL_TOKEN, {"agent": agent_name, "content": token}, session_id=ws_sid, topic=Topic.COUNCIL)
            except Exception as e:
                full_response = f"Agent {agent_name} unavailable: {e}"
                yield f"data: {json.dumps({'type': 'agent_error', 'agent': agent_name, 'error': str(e)})}\n\n"
                await emit_event(EventType.COUNCIL_AGENT_ERROR, {"agent": agent_name, "error": str(e)}, session_id=ws_sid, topic=Topic.COUNCIL)

            agent_outputs[agent_name] = full_response
            yield f"data: {json.dumps({'type': 'agent_done', 'agent': agent_name})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_DONE, {"agent": agent_name}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Moderator synthesis
        yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'moderator'})}\n\n"
        await emit_event(EventType.COUNCIL_AGENT_START, {"agent": "moderator"}, session_id=ws_sid, topic=Topic.COUNCIL)

        synth_prompt = (
            f"{MODERATOR_PROMPT}\n\n"
            f"Query: {request.query}\n\n"
            f"Agent outputs:\n"
        )
        for name, output in agent_outputs.items():
            synth_prompt += f"\n--- {name.upper()} ---\n{output}\n"

        synth_messages = [
            {"role": "system", "content": MODERATOR_PROMPT},
            {"role": "user", "content": synth_prompt},
        ]

        synthesis = ""
        try:
            async for token in llm_router.stream_with_fallback("moderator", synth_messages):
                synthesis += token
                yield f"data: {json.dumps({'type': 'token', 'agent': 'moderator', 'content': token})}\n\n"
                await emit_event(EventType.COUNCIL_TOKEN, {"agent": "moderator", "content": token}, session_id=ws_sid, topic=Topic.COUNCIL)
        except Exception as e:
            synthesis = f"Synthesis failed: {e}"
            yield f"data: {json.dumps({'type': 'agent_error', 'agent': 'moderator', 'error': str(e)})}\n\n"
            await emit_event(EventType.COUNCIL_AGENT_ERROR, {"agent": "moderator", "error": str(e)}, session_id=ws_sid, topic=Topic.COUNCIL)

        yield f"data: {json.dumps({'type': 'agent_done', 'agent': 'moderator'})}\n\n"
        await emit_event(EventType.COUNCIL_AGENT_DONE, {"agent": "moderator"}, session_id=ws_sid, topic=Topic.COUNCIL)

        # Send final result
        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'recommendation': synthesis})}\n\n"
        await emit_event(EventType.COUNCIL_COMPLETE, {"session_id": session_id, "recommendation": synthesis}, session_id=ws_sid, topic=Topic.COUNCIL)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/export/{session_id}")
async def export_council_pdf(session_id: str):
    """Export a council session as a PDF report."""
    try:
        from backend.tools.pdf_export import generate_pdf
    except ImportError:
        raise HTTPException(500, "PDF export not available (reportlab not installed)")

    # Build session data from stored results or placeholder
    session_data = {
        "session_id": session_id,
        "query": "Council session export",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent_outputs": [],
        "debate_history": [],
        "recommendation": "Session data not persisted yet — export shows template.",
        "risk_scores": [],
    }

    # Try to load from Redis first, then DB
    try:
        from backend.db.redis_client import cache_get
        cached = await cache_get(f"council_session:{session_id}")
        if cached:
            session_data.update(cached)
    except Exception:
        pass

    # Try DB if Redis didn't have it
    if session_data.get("recommendation") == "Session data not persisted yet — export shows template.":
        try:
            from backend.db.neon import execute_query
            rows = await execute_query(
                "SELECT * FROM council_sessions WHERE session_id = $1", session_id
            )
            if rows:
                row = dict(rows[0])
                session_data["query"] = row.get("query", session_data["query"])
                session_data["recommendation"] = row.get("recommendation", session_data["recommendation"])
                session_data["timestamp"] = str(row.get("created_at", session_data["timestamp"]))
                if row.get("agent_outputs"):
                    import json as _json
                    session_data["agent_outputs"] = _json.loads(row["agent_outputs"]) if isinstance(row["agent_outputs"], str) else row["agent_outputs"]
                if row.get("risk_scores"):
                    import json as _json
                    session_data["risk_scores"] = _json.loads(row["risk_scores"]) if isinstance(row["risk_scores"], str) else row["risk_scores"]
        except Exception:
            pass

    try:
        pdf_bytes = await generate_pdf(session_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=council_{session_id[:8]}.pdf"},
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(500, f"PDF export failed: {e}")
