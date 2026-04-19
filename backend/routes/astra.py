"""Astra ⭐ Simulation API routes — Parallel swarm intelligence for Council.

Astra runs automatically alongside the Council of Debate to provide:
  POST /astra/run       — Run a full simulation (graph → personas → simulate → report)
  POST /astra/chat      — Chat with simulation results (follow-up questions)
  POST /astra/review    — Run review swarm on an agent output
  GET  /astra/{id}      — Get simulation state
  POST /astra/swarm     — Run parallel brand + market simulations (auto-triggered by Council)
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

class AstraRunRequest(BaseModel):
    query: str = Field(..., description="Scenario/prediction question")
    agent_type: str = Field(default="brand", description="Agent requesting simulation (brand/market)")
    horizon_days: int = Field(default=30, ge=1, le=365)
    num_personas: int = Field(default=50, ge=2, le=200)
    rounds: int = Field(default=3, ge=1, le=10)
    focus_areas: List[str] = Field(default_factory=list)
    stream: bool = Field(default=True, description="Stream results via SSE")


class AstraChatRequest(BaseModel):
    simulation_id: str = Field(..., description="Simulation ID to chat with")
    question: str = Field(..., description="Follow-up question")


class ReviewRequest(BaseModel):
    agent_name: str = Field(..., description="Agent being reviewed")
    output: str = Field(..., description="Agent output text")
    sources: List[str] = Field(default_factory=list)
    min_score: float = Field(default=0.6, ge=0.0, le=1.0)


# ── In-memory simulation store (session-only) ───────────────────────────────────

_astra_store: dict[str, dict] = {}


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/run")
async def run_astra_simulation(request: AstraRunRequest):
    """Run an Astra ⭐ simulation. Streams progress via SSE if stream=True."""

    from backend.astra.simulation_engine import SimulationEngine

    sim_id = uuid.uuid4().hex[:12]

    if request.stream:
        async def _stream():
            yield f"data: {json.dumps({'type': 'astra_start', 'simulation_id': sim_id, 'agent_type': request.agent_type})}\n\n"

            engine = SimulationEngine()

            # Phase 1: Build graph
            yield f"data: {json.dumps({'type': 'astra_progress', 'phase': 'graph_building', 'simulation_id': sim_id})}\n\n"

            from backend.astra.graph_builder import GraphBuilder
            graph_builder = GraphBuilder()
            entities, relationships = await graph_builder.build_graph(request.query, fast_mode=True)
            entity_names = [e.name for e in entities]

            yield f"data: {json.dumps({'type': 'astra_graph_ready', 'simulation_id': sim_id, 'entities': entity_names, 'entity_count': len(entities), 'relationship_count': len(relationships)})}\n\n"

            # Phase 2: Generate personas
            yield f"data: {json.dumps({'type': 'astra_progress', 'phase': 'persona_generation', 'simulation_id': sim_id})}\n\n"

            from backend.astra.persona_generator import PersonaGenerator
            from backend.astra.schemas import SimulationConfig, SimulationState

            config = SimulationConfig(
                name=f"{request.agent_type}_astra_{sim_id}",
                seed_query=request.query,
                horizon_days=request.horizon_days,
                num_personas=request.num_personas,
                rounds=request.rounds,
                focus_areas=request.focus_areas,
            )

            persona_gen = PersonaGenerator()
            personas = await persona_gen.generate_personas(entities, relationships, config)
            persona_names = [f"{p.name} ({p.role.value})" for p in personas]

            yield f"data: {json.dumps({'type': 'astra_personas_ready', 'simulation_id': sim_id, 'personas': persona_names, 'persona_count': len(personas)})}\n\n"

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

            # Phase 3: Run simulation
            yield f"data: {json.dumps({'type': 'astra_progress', 'phase': 'simulation_running', 'simulation_id': sim_id})}\n\n"

            state = await engine.run_simulation(state)

            for rd in state.rounds:
                yield f"data: {json.dumps({'type': 'astra_round', 'simulation_id': sim_id, 'round': rd.round_number, 'events': rd.events[:5], 'sentiment_shift': rd.sentiment_shift})}\n\n"

            # Phase 4: Generate report
            yield f"data: {json.dumps({'type': 'astra_progress', 'phase': 'report_generation', 'simulation_id': sim_id})}\n\n"

            from backend.astra.report_agent import ReportAgent
            report_agent = ReportAgent()
            report = await report_agent.generate_report(state, report_type="full")

            # Store result
            _astra_store[sim_id] = {
                "state": state.model_dump(),
                "report": report,
            }

            # Final event
            yield f"data: {json.dumps({'type': 'astra_complete', 'simulation_id': sim_id, 'result': state.result.model_dump() if state.result else None, 'report_summary': {'prediction': report.get('prediction', ''), 'confidence': report.get('confidence', 0), 'key_factors': report.get('key_factors', []), 'risks': report.get('risks', []), 'opportunities': report.get('opportunities', []), 'recommendations': report.get('recommendations', [])}})}\n\n"

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

        _astra_store[sim_id] = {
            "state": state.model_dump(),
        }

        return {
            "simulation_id": sim_id,
            "status": state.status,
            "result": state.result.model_dump() if state.result else None,
        }


@router.post("/chat")
async def chat_astra(request: AstraChatRequest):
    """Chat with a completed Astra simulation — ask follow-up questions."""

    sim_data = _astra_store.get(request.simulation_id)
    if not sim_data:
        return {"error": f"Astra simulation {request.simulation_id} not found"}

    from backend.astra.schemas import SimulationState
    from backend.astra.report_agent import ReportAgent

    state = SimulationState(**sim_data["state"])
    report_agent = ReportAgent()
    answer = await report_agent.chat_with_simulation(state, request.question)

    return {"simulation_id": request.simulation_id, "answer": answer}


@router.get("/{simulation_id}")
async def get_astra_simulation(simulation_id: str):
    """Get a stored Astra simulation state."""

    sim_data = _astra_store.get(simulation_id)
    if not sim_data:
        return {"error": f"Astra simulation {simulation_id} not found"}

    return sim_data


class AstraSwarmRequest(BaseModel):
    query: str = Field(..., description="Scenario/prediction question for Astra swarm simulation")
    horizon_days: int = Field(default=30, ge=1, le=365)
    num_personas: int = Field(default=50, ge=2, le=200)
    rounds: int = Field(default=3, ge=1, le=10)


@router.post("/swarm")
async def run_astra_swarm(request: AstraSwarmRequest):
    """Run Astra ⭐ swarm simulation for brand + market agents in parallel.
    
    This endpoint is automatically triggered when the Council of Debate runs,
    providing parallel predictive intelligence.
    """

    async def _run_agent(agent_type: str, queue: asyncio.Queue):
        """Run Astra simulation for a single agent."""
        from backend.astra.simulation_engine import SimulationEngine
        from backend.astra.graph_builder import GraphBuilder
        from backend.astra.persona_generator import PersonaGenerator
        from backend.astra.schemas import SimulationConfig, SimulationState

        sim_id = f"{agent_type}_astra_{uuid.uuid4().hex[:8]}"

        def _emit(event_data: dict):
            queue.put_nowait(f"data: {json.dumps(event_data)}\n\n")

        try:
            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'graph_building', 'simulation_id': sim_id})
            graph_builder = GraphBuilder()
            entities, relationships = await graph_builder.build_graph(request.query, fast_mode=True)
            entity_names = [e.name for e in entities]

            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'graph_ready', 'simulation_id': sim_id, 'entities': entity_names, 'entity_count': len(entities)})

            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'persona_generation', 'simulation_id': sim_id})
            config = SimulationConfig(
                name=sim_id,
                seed_query=request.query,
                horizon_days=request.horizon_days,
                num_personas=request.num_personas,
                rounds=request.rounds,
            )
            persona_gen = PersonaGenerator()
            personas = await persona_gen.generate_personas(entities, relationships, config)
            persona_names = [f"{p.name} ({p.role.value})" for p in personas]

            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'personas_ready', 'simulation_id': sim_id, 'personas': persona_names, 'persona_count': len(personas)})

            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'simulation_running', 'simulation_id': sim_id})
            state = SimulationState(
                id=sim_id,
                config=config,
                entities=entities,
                relationships=relationships,
                personas=personas,
                agent_type=agent_type,
                parent_query=request.query,
            )
            engine = SimulationEngine()
            state = await engine.run_simulation(state)

            _emit({'type': 'astra_agent_progress', 'agent': agent_type, 'phase': 'report_generation', 'simulation_id': sim_id})
            from backend.astra.report_agent import ReportAgent
            report_agent = ReportAgent()
            report = await report_agent.generate_report(state, report_type="full")

            result = {
                "simulation_id": sim_id,
                "status": state.status,
                "prediction": state.result.prediction if state.result else "Simulation failed",
                "confidence": state.result.confidence if state.result else 0.0,
                "key_factors": state.result.key_factors if state.result else [],
                "risks": state.result.risks if state.result else [],
                "opportunities": state.result.opportunities if state.result else [],
                "recommendations": state.result.recommendations if state.result else [],
                "scenarios": report.get("scenarios", state.result.scenarios if state.result else []),
                "entities": entity_names,
                "personas": persona_names,
            }

            _emit({'type': 'astra_agent_complete', 'agent': agent_type, 'result': result})

            _astra_store[sim_id] = {
                "state": state.model_dump(),
                "report": report,
            }

        except Exception as e:
            logger.error(f"Astra swarm simulation for {agent_type} failed: {e}")
            _emit({'type': 'astra_agent_error', 'agent': agent_type, 'error': str(e)})

    async def _stream():
        queue: asyncio.Queue[str] = asyncio.Queue()

        yield f"data: {json.dumps({'type': 'astra_start', 'agents': ['brand', 'market']})}\n\n"

        async def _producer():
            await asyncio.gather(
                _run_agent("brand", queue),
                _run_agent("market", queue),
            )
            await queue.put(None)

        producer_task = asyncio.create_task(_producer())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

        yield f"data: {json.dumps({'type': 'astra_complete'})}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
