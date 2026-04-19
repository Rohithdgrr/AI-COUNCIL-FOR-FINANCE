"""Report Agent for MiroFish - Generates analysis reports from simulation results."""

import logging
import json
import re
from typing import Optional

from backend.mirofish.schemas import SimulationState, SimulationResult
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


class ReportAgent:
    """Generates detailed reports from simulation results."""

    async def generate_report(
        self,
        state: SimulationState,
        report_type: str = "full",
    ) -> dict:
        """Generate a structured report from simulation state.

        Args:
            state: Completed simulation state
            report_type: "full", "summary", or "actionable"

        Returns:
            Report dictionary with structured sections
        """
        if not state.result:
            return {"error": "Simulation has no results yet"}

        if report_type == "summary":
            return await self._generate_summary_report(state)
        elif report_type == "actionable":
            return await self._generate_actionable_report(state)
        else:
            return await self._generate_full_report(state)

    async def _generate_full_report(self, state: SimulationState) -> dict:
        """Generate a comprehensive simulation report."""
        result = state.result

        # Build persona interaction summary
        persona_summaries = []
        for persona in state.personas:
            interactions = []
            for round_data in state.rounds:
                for interaction in round_data.interactions:
                    if interaction.get("persona_id") == persona.id:
                        interactions.append({
                            "round": round_data.round_number,
                            "response": interaction.get("response", "")[:200],
                        })
            persona_summaries.append({
                "name": persona.name,
                "role": persona.role.value,
                "traits": persona.traits,
                "key_interactions": interactions[:3],
            })

        # Build sentiment trajectory
        sentiment_trajectory = []
        for round_data in state.rounds:
            sentiment_trajectory.append({
                "round": round_data.round_number,
                "shifts": round_data.sentiment_shift,
                "events": round_data.events[:3],
            })

        report = {
            "simulation_id": state.id,
            "scenario": state.config.seed_query,
            "horizon_days": state.config.horizon_days,
            "status": state.status,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "key_factors": result.key_factors,
            "scenarios": result.scenarios,
            "risks": result.risks,
            "opportunities": result.opportunities,
            "recommendations": result.recommendations,
            "personas": persona_summaries,
            "sentiment_trajectory": sentiment_trajectory,
            "entities_count": len(state.entities),
            "relationships_count": len(state.relationships),
            "rounds_completed": len(state.rounds),
        }

        return report

    async def _generate_summary_report(self, state: SimulationState) -> dict:
        """Generate a brief summary report."""
        result = state.result
        return {
            "simulation_id": state.id,
            "scenario": state.config.seed_query,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "top_risks": result.risks[:3],
            "top_opportunities": result.opportunities[:3],
            "key_recommendation": result.recommendations[0] if result.recommendations else None,
        }

    async def _generate_actionable_report(self, state: SimulationState) -> dict:
        """Generate an action-oriented report with specific next steps."""
        result = state.result

        prompt = f"""Based on this simulation result, generate actionable next steps.

Scenario: {state.config.seed_query}
Prediction: {result.prediction}
Confidence: {result.confidence:.0%}
Key Factors: {', '.join(result.key_factors)}
Risks: {', '.join(result.risks)}
Opportunities: {', '.join(result.opportunities)}

Generate a JSON response with:
{{
  "immediate_actions": [
    {{"action": "...", "priority": "high|medium|low", "timeline": "24h|7d|30d", "owner": "brand|market|risk|supply"}}
  ],
  "monitoring_triggers": [
    {{"metric": "...", "threshold": "...", "response": "..."}}
  ],
  "decision_points": [
    {{"decision": "...", "condition": "...", "options": ["option1", "option2"]}}
  ],
  "communication_talking_points": ["point1", "point2"]
}}"""

        try:
            messages = [
                {"role": "system", "content": "You are a strategic advisor. Convert simulation predictions into concrete action plans."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                action_data = json.loads(json_match.group())
                return {
                    "simulation_id": state.id,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    **action_data,
                }
        except Exception as e:
            logger.error(f"Actionable report generation failed: {e}")

        return {
            "simulation_id": state.id,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "immediate_actions": [{"action": r, "priority": "medium", "timeline": "30d", "owner": "brand"} for r in result.recommendations],
            "monitoring_triggers": [],
            "decision_points": [],
        }

    async def chat_with_simulation(
        self,
        state: SimulationState,
        question: str,
    ) -> str:
        """Chat with the simulation results - ask follow-up questions.

        Args:
            state: Simulation state
            question: Follow-up question

        Returns:
            Answer based on simulation data
        """
        if not state.result:
            return "Simulation has no results yet. Please run the simulation first."

        # Build context from simulation state
        context_parts = [
            f"SCENARIO: {state.config.seed_query}",
            f"PREDICTION: {state.result.prediction}",
            f"CONFIDENCE: {state.result.confidence:.0%}",
            f"KEY FACTORS: {', '.join(state.result.key_factors)}",
            f"RISKS: {', '.join(state.result.risks)}",
            f"OPPORTUNITIES: {', '.join(state.result.opportunities)}",
        ]

        # Add persona perspectives
        for round_data in state.rounds[-2:]:
            for interaction in round_data.interactions[:5]:
                context_parts.append(
                    f"  {interaction.get('persona_name', 'Unknown')} ({interaction.get('persona_role', '')}): "
                    f"{interaction.get('response', '')[:200]}"
                )

        context = "\n".join(context_parts)

        messages = [
            {"role": "system", "content": f"You are a simulation analyst. Answer questions based on the simulation results below.\n\n{context}"},
            {"role": "user", "content": question},
        ]

        try:
            response_text = ""
            async for token in llm_router.stream_with_fallback("moderator", messages):
                response_text += token
            return response_text if response_text else "Unable to generate response."
        except Exception as e:
            try:
                response, _ = await llm_router.invoke_with_fallback("moderator", messages)
                return getattr(response, "content", str(response))
            except Exception as e2:
                return f"Error: {e2}"
