"""Simulation API routes — MiroFish simulation endpoints for Brand & Market agents.

Provides:
  POST /simulation/run       — Run a full simulation (graph → personas → simulate → report)
  POST /simulation/chat      — Chat with simulation results (follow-up questions)
  POST /simulation/review    — Run review swarm on an agent output
  GET  /simulation/{id}      — Get simulation state
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request Models ──────────────────────────────────────────────────────────────

class SimulationRunRequest(BaseModel):
    query: str = Field(..., description="Scenario/prediction question")
    agent_type: str = Field(default="brand", description="Agent requesting simulation (brand/market)")
    horizon_days: int = Field(default=30, ge=1, le=365)
    num_personas: int = Field(default=5, ge=2, le=20)
    rounds: int = Field(default=3, ge=1, le=10)
    focus_areas: List[str] = Field(default_factory=list)
    stream: bool = Field(default=True, description="Stream results via SSE")


class SimulationChatRequest(BaseModel):
    simulation_id: str = Field(..., description="Simulation ID to chat with")
    question: str = Field(..., description="Follow-up question")


class ReviewRequest(BaseModel):
    agent_name: str = Field(..., description="Agent being reviewed")
    output: str = Field(..., description="Agent output text")
    sources: List[str] = Field(default_factory=list)
    min_score: float = Field(default=0.6, ge=0.0, le=1.0)


# ── In-memory simulation store (session-only) ───────────────────────────────────

_simulation_store: dict[str, dict] = {}


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/run")
async def run_simulation(request: SimulationRunRequest):
    """Run a MiroFish simulation. Streams progress via SSE if stream=True."""

    from backend.mirofish.simulation_engine import SimulationEngine

    sim_id = uuid.uuid4().hex[:12]

    if request.stream:
        async def _stream():
            yield f"data: {json.dumps({'type': 'sim_start', 'simulation_id': sim_id, 'agent_type': request.agent_type})}\n\n"

            engine = SimulationEngine()

            # Phase 1: Build graph
            yield f"data: {json.dumps({'type': 'sim_progress', 'phase': 'graph_building', 'simulation_id': sim_id})}\n\n"

            from backend.mirofish.graph_builder import GraphBuilder
            graph_builder = GraphBuilder()
            entities, relationships = await graph_builder.build_graph(request.query)
            entity_names = [e.name for e in entities]

            yield f"data: {json.dumps({'type': 'sim_graph_ready', 'simulation_id': sim_id, 'entities': entity_names, 'entity_count': len(entities), 'relationship_count': len(relationships)})}\n\n"

            # Phase 2: Generate personas
            yield f"data: {json.dumps({'type': 'sim_progress', 'phase': 'persona_generation', 'simulation_id': sim_id})}\n\n"

            from backend.mirofish.persona_generator import PersonaGenerator
            from backend.mirofish.schemas import SimulationConfig, SimulationState

            config = SimulationConfig(
                name=f"{request.agent_type}_sim_{sim_id}",
                seed_query=request.query,
                horizon_days=request.horizon_days,
                num_personas=request.num_personas,
                rounds=request.rounds,
                focus_areas=request.focus_areas,
            )

            persona_gen = PersonaGenerator()
            personas = await persona_gen.generate_personas(entities, relationships, config)
            persona_names = [f"{p.name} ({p.role.value})" for p in personas]

            yield f"data: {json.dumps({'type': 'sim_personas_ready', 'simulation_id': sim_id, 'personas': persona_names, 'persona_count': len(personas)})}\n\n"

            # Build initial state
            state = SimulationState(
                id=sim_id,
                config=config,
                entities=entities,
                relationships=relationships,
                personas=personas,
                agent_type=request.agent_type,
                parent_query=request.query,
            )

            # Phase 3: Run simulation with streaming round callbacks
            async def on_round_complete(sim_state, round_result):
                yield f"data: {json.dumps({'type': 'sim_round', 'simulation_id': sim_id, 'round': round_result.round_number, 'events': round_result.events[:5], 'sentiment_shift': round_result.sentiment_shift})}\n\n"

            yield f"data: {json.dumps({'type': 'sim_progress', 'phase': 'simulation_running', 'simulation_id': sim_id})}\n\n"

            # Run simulation (non-streaming callback since we can't yield from nested async)
            state = await engine.run_simulation(state)

            for rd in state.rounds:
                yield f"data: {json.dumps({'type': 'sim_round', 'simulation_id': sim_id, 'round': rd.round_number, 'events': rd.events[:5], 'sentiment_shift': rd.sentiment_shift})}\n\n"

            # Phase 4: Generate report
            yield f"data: {json.dumps({'type': 'sim_progress', 'phase': 'report_generation', 'simulation_id': sim_id})}\n\n"

            from backend.mirofish.report_agent import ReportAgent
            report_agent = ReportAgent()
            report = await report_agent.generate_report(state, report_type="full")

            # Store result
            _simulation_store[sim_id] = {
                "state": state.model_dump(),
                "report": report,
            }

            # Final event
            yield f"data: {json.dumps({'type': 'sim_complete', 'simulation_id': sim_id, 'result': state.result.model_dump() if state.result else None, 'report_summary': {'prediction': report.get('prediction', ''), 'confidence': report.get('confidence', 0), 'key_factors': report.get('key_factors', []), 'risks': report.get('risks', []), 'opportunities': report.get('opportunities', []), 'recommendations': report.get('recommendations', [])}})}\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    else:
        # Non-streaming: run synchronously
        engine = SimulationEngine()
        state = await engine.run_quick_simulation(
            query=request.query,
            agent_type=request.agent_type,
            horizon_days=request.horizon_days,
            num_personas=request.num_personas,
            rounds=request.rounds,
        )

        _simulation_store[sim_id] = {
            "state": state.model_dump(),
        }

        return {
            "simulation_id": sim_id,
            "status": state.status,
            "result": state.result.model_dump() if state.result else None,
        }


@router.post("/chat")
async def chat_simulation(request: SimulationChatRequest):
    """Chat with a completed simulation — ask follow-up questions."""

    sim_data = _simulation_store.get(request.simulation_id)
    if not sim_data:
        return {"error": f"Simulation {request.simulation_id} not found"}

    from backend.mirofish.schemas import SimulationState
    from backend.mirofish.report_agent import ReportAgent

    state = SimulationState(**sim_data["state"])
    report_agent = ReportAgent()
    answer = await report_agent.chat_with_simulation(state, request.question)

    return {"simulation_id": request.simulation_id, "answer": answer}


@router.post("/review")
async def review_output(request: ReviewRequest):
    """Run the review swarm on an agent output."""

    from backend.agents.review_swarm import ReviewSwarm

    swarm = ReviewSwarm()
    result = await swarm.review_output(
        agent_name=request.agent_name,
        output=request.output,
        sources=request.sources,
        min_score=request.min_score,
    )

    return result.model_dump()


@router.get("/{simulation_id}")
async def get_simulation(simulation_id: str):
    """Get a stored simulation state."""

    sim_data = _simulation_store.get(simulation_id)
    if not sim_data:
        return {"error": f"Simulation {simulation_id} not found"}

    return sim_data
