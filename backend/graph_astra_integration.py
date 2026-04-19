"""Astra ⭐ Integration Node for Council of Debate.

This node automatically triggers Astra simulations in parallel with the Council,
providing predictive intelligence and scenario forecasting.
"""

import asyncio
import logging
from backend.state import CouncilState
from backend.graph_utils import node_error_handler

logger = logging.getLogger(__name__)


@node_error_handler(fallback={"astra_results": None})
async def astra_parallel_node(state: CouncilState) -> dict:
    """Run Astra ⭐ simulations in parallel with Council debate.
    
    Automatically triggers brand and market simulations to provide:
    - Future scenario predictions
    - Multi-agent swarm intelligence
    - Risk and opportunity forecasting
    - Sentiment trajectory analysis
    
    Returns:
        dict with astra_results containing brand and market simulation outputs
    """
    query = state.get("query", "")
    if not query:
        return {"astra_results": None}
    
    context = state.get("context") or {}
    
    # Check if Astra is explicitly disabled
    if context.get("disable_astra", False):
        logger.info("Astra simulations disabled by context flag")
        return {"astra_results": None}
    
    logger.info(f"⭐ Astra: Starting parallel simulations for query: {query[:60]}...")
    
    try:
        from backend.astra.simulation_engine import SimulationEngine
        from backend.astra.graph_builder import GraphBuilder
        from backend.astra.persona_generator import PersonaGenerator
        from backend.astra.schemas import SimulationConfig, SimulationState
        
        async def run_agent_simulation(agent_type: str) -> dict:
            """Run a single Astra simulation for an agent."""
            try:
                sim_id = f"{agent_type}_astra_{state.get('session_id', 'unknown')[:8]}"
                
                # Phase 1: Build graph (fast mode)
                graph_builder = GraphBuilder()
                entities, relationships = await graph_builder.build_graph(query, fast_mode=True)
                
                # Phase 2: Generate personas (reduced count for speed)
                config = SimulationConfig(
                    name=sim_id,
                    seed_query=query,
                    horizon_days=30,
                    num_personas=20,  # Reduced for parallel execution
                    rounds=2,  # Reduced for speed
                )
                
                persona_gen = PersonaGenerator()
                personas = await persona_gen.generate_personas(entities, relationships, config)
                
                # Phase 3: Run simulation
                sim_state = SimulationState(
                    id=sim_id,
                    config=config,
                    entities=entities,
                    relationships=relationships,
                    personas=personas,
                    agent_type=agent_type,
                    parent_query=query,
                )
                
                engine = SimulationEngine()
                sim_state = await engine.run_simulation(sim_state)
                
                # Phase 4: Generate report
                from backend.astra.report_agent import ReportAgent
                report_agent = ReportAgent()
                report = await report_agent.generate_report(sim_state, report_type="summary")
                
                return {
                    "agent": agent_type,
                    "simulation_id": sim_id,
                    "status": sim_state.status,
                    "prediction": sim_state.result.prediction if sim_state.result else "No prediction",
                    "confidence": sim_state.result.confidence if sim_state.result else 0.0,
                    "key_factors": sim_state.result.key_factors if sim_state.result else [],
                    "risks": sim_state.result.risks if sim_state.result else [],
                    "opportunities": sim_state.result.opportunities if sim_state.result else [],
                    "recommendations": sim_state.result.recommendations if sim_state.result else [],
                    "scenarios": sim_state.result.scenarios if sim_state.result else [],
                    "entity_count": len(entities),
                    "persona_count": len(personas),
                    "rounds_completed": len(sim_state.rounds),
                }
            except Exception as e:
                logger.error(f"Astra simulation for {agent_type} failed: {e}")
                return {
                    "agent": agent_type,
                    "status": "failed",
                    "error": str(e),
                }
        
        # Run brand and market simulations in parallel
        brand_task = run_agent_simulation("brand")
        market_task = run_agent_simulation("market")
        
        brand_result, market_result = await asyncio.gather(brand_task, market_task, return_exceptions=True)
        
        astra_results = {
            "brand": brand_result if not isinstance(brand_result, Exception) else {"status": "failed", "error": str(brand_result)},
            "market": market_result if not isinstance(market_result, Exception) else {"status": "failed", "error": str(market_result)},
            "enabled": True,
        }
        
        logger.info(
            f"⭐ Astra: Simulations complete - "
            f"Brand: {astra_results['brand'].get('status', 'unknown')}, "
            f"Market: {astra_results['market'].get('status', 'unknown')}"
        )
        
        return {"astra_results": astra_results}
        
    except Exception as e:
        logger.error(f"Astra parallel execution failed: {e}")
        return {"astra_results": {"enabled": False, "error": str(e)}}
