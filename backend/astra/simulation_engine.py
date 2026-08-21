"""Astra ⭐ Simulation Engine - Runs parallel multi-agent simulations.

Astra automatically runs alongside the Council of Debate to provide:
- Predictive scenario simulations
- Multi-agent swarm intelligence
- Future state forecasting
- Risk and opportunity identification
"""

import asyncio
import logging
import json
import re
from typing import List, Optional, Callable
from datetime import datetime
from uuid import uuid4

from backend.astra.schemas import (
    Persona, SimulationConfig, SimulationState, SimulationRound, SimulationResult
)
from backend.astra.memory_manager import MemoryManager
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Runs multi-agent simulations with parallel persona interactions."""

    def __init__(self):
        self.memory_manager = MemoryManager()

    async def run_simulation(
        self,
        state: SimulationState,
        on_round_complete: Optional[Callable] = None,
    ) -> SimulationState:
        """Run the full simulation pipeline.

        Args:
            state: Initial simulation state with entities, personas, config
            on_round_complete: Optional callback after each round

        Returns:
            Updated SimulationState with results
        """
        state.status = "running"
        state.updated_at = datetime.utcnow()
        logger.info(f"Starting simulation '{state.config.name}' with {len(state.personas)} personas")

        try:
            for round_num in range(1, state.config.rounds + 1):
                logger.info(f"Simulation round {round_num}/{state.config.rounds}")

                # Run all personas in parallel for this round
                round_result = await self._run_round(state, round_num)

                state.rounds.append(round_result)

                # Update persona memories after each round
                self.memory_manager.update_memories(state.personas, round_result)

                # Inject temporal context
                self.memory_manager.inject_temporal_context(
                    state.personas, round_num, state.config.horizon_days
                )

                state.updated_at = datetime.utcnow()

                if on_round_complete:
                    try:
                        await on_round_complete(state, round_result)
                    except Exception as cb_err:
                        logger.error(f"Round callback failed: {cb_err}")

            # Generate final result
            state.result = await self._synthesize_result(state)
            state.status = "completed"
            state.updated_at = datetime.utcnow()

            logger.info(
                f"Simulation complete: confidence={state.result.confidence:.0%}, "
                f"prediction={state.result.prediction[:100]}..."
            )

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            state.status = "failed"
            state.updated_at = datetime.utcnow()

        return state

    async def _run_round(
        self,
        state: SimulationState,
        round_num: int,
    ) -> SimulationRound:
        """Run a single simulation round. Batches personas by role for speed."""
        interactions = []
        events = []

        # Build context for this round
        round_context = self._build_round_context(state, round_num)

        # Group personas by role for batched LLM calls (8 calls vs 50+)
        role_groups: dict[str, list[Persona]] = {}
        for persona in state.personas:
            role_groups.setdefault(persona.role.value, []).append(persona)

        # Run each role group as a single batched LLM call in parallel
        async def _run_role_batch(role: str, personas: list[Persona]) -> list[dict]:
            try:
                batch_responses = await self._get_batch_persona_responses(personas, role, round_context, state.config)
                return batch_responses
            except Exception as e:
                logger.error(f"Role batch {role} failed in round {round_num}: {e}")
                return [{
                    "persona_id": p.id,
                    "persona_name": p.name,
                    "persona_role": p.role.value,
                    "response": f"Error: {e}",
                    "timestamp": datetime.utcnow().isoformat(),
                } for p in personas]

        batch_tasks = [_run_role_batch(role, group) for role, group in role_groups.items()]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, list):
                for interaction in result:
                    if isinstance(interaction, dict):
                        interactions.append(interaction)
                        if "error" not in interaction.get("response", "").lower():
                            events.append(f"{interaction['persona_name']} ({interaction['persona_role']}): {interaction['response'][:100]}")

        # Calculate sentiment shift for this round
        sentiment_shift = self._calculate_sentiment_shift(interactions)

        return SimulationRound(
            round_number=round_num,
            timestamp=datetime.utcnow(),
            interactions=interactions,
            events=events,
            sentiment_shift=sentiment_shift,
        )

    def _build_round_context(self, state: SimulationState, round_num: int) -> str:
        """Build context string for a simulation round."""
        day_offset = int((round_num / state.config.rounds) * state.config.horizon_days)

        context_parts = [
            f"SCENARIO: {state.config.seed_query}",
            f"TIME: Day {day_offset} of {state.config.horizon_days}-day simulation",
            f"ROUND: {round_num} of {state.config.rounds}",
        ]

        # Include previous round summaries
        if state.rounds:
            last_round = state.rounds[-1]
            context_parts.append(f"PREVIOUS EVENTS: {'; '.join(last_round.events[:3])}")
            if last_round.sentiment_shift:
                shifts = "; ".join(f"{k}: {v:+.1f}" for k, v in last_round.sentiment_shift.items())
                context_parts.append(f"SENTIMENT SHIFTS: {shifts}")

        # Include focus areas
        if state.config.focus_areas:
            context_parts.append(f"FOCUS AREAS: {', '.join(state.config.focus_areas)}")

        return "\n".join(context_parts)

    async def _get_batch_persona_responses(
        self,
        personas: list[Persona],
        role: str,
        round_context: str,
        config: SimulationConfig,
    ) -> list[dict]:
        """Get responses for all personas of a given role in a single batched LLM call."""
        persona_descriptions = []
        for p in personas:
            memory_str = "; ".join(p.memory[-3:]) if p.memory else "No prior context"
            persona_descriptions.append(
                f"  - {p.name}: traits=[{', '.join(p.traits[:3])}], goals=[{', '.join(p.goals[:2])}], memory={memory_str[:100]}"
            )

        persona_list_str = "\n".join(persona_descriptions)

        prompt = f"""You are simulating {len(personas)} personas with the '{role}' role in a supply chain scenario.

SCENARIO CONTEXT:
{round_context}

PERSONAS (all {role} role):
{persona_list_str}

For EACH persona, provide their response to the scenario. Return as JSON array:
[
  {{"name": "persona name", "response": "their specific reaction and actions (2-3 sentences)"}}
]

Make each persona's response unique based on their traits and goals. Be specific and realistic."""

        messages = [
            {"role": "system", "content": f"You are a multi-persona simulation engine. Generate responses for multiple {role} personas simultaneously."},
            {"role": "user", "content": prompt},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                results = []
                for i, item in enumerate(data[:len(personas)]):
                    p = personas[i] if i < len(personas) else personas[-1]
                    results.append({
                        "persona_id": p.id,
                        "persona_name": p.name,
                        "persona_role": p.role.value,
                        "response": item.get("response", item.get("reaction", "No response")),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                # Fill any missing personas
                while len(results) < len(personas):
                    p = personas[len(results)]
                    results.append({
                        "persona_id": p.id,
                        "persona_name": p.name,
                        "persona_role": p.role.value,
                        "response": f"{p.name} concurs with the {role} consensus.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                return results
        except Exception as e:
            logger.error(f"Batch LLM call failed for role {role}: {e}")

        # Fallback: generate simple responses without LLM
        return [{
            "persona_id": p.id,
            "persona_name": p.name,
            "persona_role": p.role.value,
            "response": f"{p.name} ({role}) assesses the situation based on {', '.join(p.traits[:2])} perspective.",
            "timestamp": datetime.utcnow().isoformat(),
        } for p in personas]

    def _calculate_sentiment_shift(self, interactions: list) -> dict:
        """Calculate sentiment shifts from persona interactions."""
        shifts = {"overall": 0.0, "confidence": 0.0, "risk": 0.0}

        for interaction in interactions:
            response = interaction.get("response", "").lower()
            # Simple heuristic sentiment analysis
            positive_words = ["growth", "opportunity", "improve", "benefit", "advantage", "strong", "positive"]
            negative_words = ["decline", "risk", "threat", "loss", "disruption", "weak", "negative", "crisis"]

            pos_count = sum(1 for w in positive_words if w in response)
            neg_count = sum(1 for w in negative_words if w in response)

            if pos_count > neg_count:
                shifts["overall"] += 0.1
                shifts["confidence"] += 0.05
            elif neg_count > pos_count:
                shifts["overall"] -= 0.1
                shifts["risk"] += 0.05

        return shifts

    async def _synthesize_result(self, state: SimulationState) -> SimulationResult:
        """Synthesize final simulation result from all rounds."""
        # Collect all interactions
        all_interactions = []
        for round_data in state.rounds:
            for interaction in round_data.interactions:
                all_interactions.append(
                    f"Round {round_data.round_number} - {interaction.get('persona_name', 'Unknown')} "
                    f"({interaction.get('persona_role', 'unknown')}): {interaction.get('response', '')[:300]}"
                )

        interactions_text = "\n".join(all_interactions[:20])

        # Calculate overall sentiment trajectory
        sentiment_trajectory = []
        for round_data in state.rounds:
            sentiment_trajectory.append(round_data.sentiment_shift.get("overall", 0.0))

        prompt = f"""Synthesize the following simulation results into a clear prediction.

SCENARIO: {state.config.seed_query}
HORIZON: {state.config.horizon_days} days
PERSONAS INVOLVED: {', '.join(p.name for p in state.personas)}

SIMULATION INTERACTIONS:
{interactions_text}

SENTIMENT TRAJECTURE: {sentiment_trajectory}

Provide your analysis as JSON:
{{
  "prediction": "Main prediction in 2-3 sentences",
  "confidence": 0.0 to 1.0,
  "key_factors": ["factor1", "factor2", "factor3"],
  "scenarios": [
    {{"name": "Best case", "probability": 0.2, "description": "..."}},
    {{"name": "Most likely", "probability": 0.6, "description": "..."}},
    {{"name": "Worst case", "probability": 0.2, "description": "..."}}
  ],
  "risks": ["risk1", "risk2"],
  "opportunities": ["opp1", "opp2"],
  "recommendations": ["rec1", "rec2"]
}}"""

        try:
            messages = [
                {"role": "system", "content": "You are a simulation analysis expert. Synthesize multi-agent simulation results into actionable predictions."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return SimulationResult(
                    prediction=data.get("prediction", "No prediction generated"),
                    confidence=data.get("confidence", 0.5),
                    key_factors=data.get("key_factors", []),
                    scenarios=data.get("scenarios", []),
                    risks=data.get("risks", []),
                    opportunities=data.get("opportunities", []),
                    recommendations=data.get("recommendations", []),
                )
        except Exception as e:
            logger.error(f"Result synthesis failed: {e}")

        # Fallback result
        return SimulationResult(
            prediction=f"Simulation completed with {len(state.personas)} personas over {state.config.rounds} rounds. Sentiment trajectory: {sentiment_trajectory}",
            confidence=0.5,
            key_factors=["simulation_completed"],
            risks=["incomplete_analysis"],
            opportunities=["further_simulation_recommended"],
            recommendations=["run_additional_rounds"],
        )

    async def run_quick_simulation(
        self,
        query: str,
        agent_type: str = "brand",
        horizon_days: int = 30,
        num_personas: int = 5,
        rounds: int = 3,
    ) -> SimulationState:
        """Convenience method: run a complete simulation from just a query.

        Args:
            query: The scenario/prediction question
            agent_type: Which agent is requesting (brand/market)
            horizon_days: Simulation horizon
            num_personas: Number of personas
            rounds: Number of simulation rounds

        Returns:
            Complete SimulationState with results
        """
        from backend.astra.graph_builder import GraphBuilder
        from backend.astra.persona_generator import PersonaGenerator

        config = SimulationConfig(
            name=f"{agent_type}_sim_{uuid4().hex[:6]}",
            seed_query=query,
            horizon_days=horizon_days,
            num_personas=num_personas,
            rounds=rounds,
        )

        state = SimulationState(
            id=uuid4().hex[:12],
            config=config,
            agent_type=agent_type,
            parent_query=query,
        )

        # Build graph
        graph_builder = GraphBuilder()
        entities, relationships = await graph_builder.build_graph(query, fast_mode=True)
        state.entities = entities
        state.relationships = relationships

        # Generate personas
        persona_gen = PersonaGenerator()
        personas = await persona_gen.generate_personas(entities, relationships, config)
        state.personas = personas

        # Run simulation
        state = await self.run_simulation(state)

        return state
