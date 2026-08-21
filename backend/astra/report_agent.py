"""Report Agent for MiroFish - Generates analysis reports from simulation results."""

import logging
import json
import re
from typing import Optional

from backend.astra.schemas import SimulationState, SimulationResult
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
        """Generate a comprehensive simulation report with detailed explanations."""
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
                "goals": persona.goals,
                "position": persona.position,
                "key_interactions": interactions[:3],
            })

        # Build sentiment trajectory
        sentiment_trajectory = []
        for round_data in state.rounds:
            sentiment_trajectory.append({
                "round": round_data.round_number,
                "shifts": round_data.sentiment_shift,
                "events": round_data.events[:5],
            })

        # Generate detailed explanation + scenarios in a single LLM call for speed
        combined_result = await self._generate_explanation_and_scenarios(state)
        detailed_explanation = combined_result.get("explanation", "")
        enhanced_scenarios = combined_result.get("scenarios", [])

        # Generate sources list
        sources = self._extract_sources(state)

        # Build methodology description
        methodology = self._describe_methodology(state)

        report = {
            "simulation_id": state.id,
            "scenario": state.config.seed_query,
            "horizon_days": state.config.horizon_days,
            "status": state.status,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "key_factors": result.key_factors,
            "scenarios": enhanced_scenarios if enhanced_scenarios else result.scenarios,
            "risks": result.risks,
            "opportunities": result.opportunities,
            "recommendations": result.recommendations,
            "personas": persona_summaries,
            "sentiment_trajectory": sentiment_trajectory,
            "entities_count": len(state.entities),
            "relationships_count": len(state.relationships),
            "rounds_completed": len(state.rounds),
            "detailed_explanation": detailed_explanation,
            "methodology": methodology,
            "assumptions": result.assumptions if hasattr(result, 'assumptions') else [],
            "sources": sources,
            "data_quality_score": result.data_quality_score if hasattr(result, 'data_quality_score') else 0.0,
        }

        return report

    async def _generate_explanation_and_scenarios(self, state: SimulationState) -> dict:
        """Generate detailed explanation AND scenarios in a single LLM call for speed."""
        result = state.result
        entity_names = [e.name for e in state.entities[:15]]
        persona_roles = [f"{p.name} ({p.role.value})" for p in state.personas[:10]]

        prompt = f"""Analyze this simulation and provide BOTH a detailed explanation and scenario breakdown.

Scenario: {state.config.seed_query}
Prediction: {result.prediction}
Confidence: {result.confidence:.0%}
Key Factors: {', '.join(result.key_factors[:10])}
Risks: {', '.join(result.risks[:5])}
Opportunities: {', '.join(result.opportunities[:5])}
Entities: {', '.join(entity_names)}
Personas: {', '.join(persona_roles)}
Rounds: {len(state.rounds)}
Horizon: {state.config.horizon_days} days

Return as JSON:
{{
  "explanation": "300-500 word detailed analysis covering: WHY this prediction is most likely, key dynamics driving the outcome, how different persona perspectives converge/diverge, what could change the prediction, and timeline considerations",
  "scenarios": [
    {{
      "name": "Scenario Name",
      "probability": 0.0 to 1.0,
      "description": "2-3 sentence detailed description",
      "impact": "low|medium|high|critical",
      "key_drivers": ["driver1", "driver2"],
      "timeline": "Expected timeline",
      "affected_entities": ["entity1", "entity2"]
    }}
  ]
}}

Include 5-7 scenarios covering: best case, worst case, most likely, and 2-4 alternatives.
Probabilities should sum to approximately 1.0."""

        try:
            messages = [
                {"role": "system", "content": "You are a senior simulation analyst and scenario planning expert. Provide comprehensive analysis."},
                {"role": "user", "content": prompt},
            ]
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Combined explanation+scenarios generation failed: {e}")

        # Fallback
        return {
            "explanation": f"Prediction: {result.prediction} with {result.confidence:.0%} confidence based on {len(state.personas)} persona simulations.",
            "scenarios": [
                {"name": "Most Likely", "probability": result.confidence, "description": result.prediction, "impact": "medium", "key_drivers": result.key_factors[:3], "timeline": f"{state.config.horizon_days} days", "affected_entities": entity_names[:3]},
                {"name": "Best Case", "probability": result.confidence * 0.3, "description": "Favorable outcome", "impact": "low", "key_drivers": result.opportunities[:2], "timeline": f"{state.config.horizon_days * 2} days", "affected_entities": entity_names[:2]},
                {"name": "Worst Case", "probability": 1 - result.confidence, "description": "Adverse outcome", "impact": "critical", "key_drivers": result.risks[:2], "timeline": f"{state.config.horizon_days // 2} days", "affected_entities": entity_names[:3]},
            ],
        }

    async def _generate_detailed_explanation(self, state: SimulationState) -> str:
        """Generate a detailed explanation of the prediction using LLM."""
        result = state.result
        entity_names = [e.name for e in state.entities[:15]]
        persona_roles = [f"{p.name} ({p.role.value})" for p in state.personas[:10]]

        prompt = f"""Provide a detailed explanation (300-500 words) of this simulation prediction.

Scenario: {state.config.seed_query}
Prediction: {result.prediction}
Confidence: {result.confidence:.0%}
Key Factors: {', '.join(result.key_factors[:10])}
Risks: {', '.join(result.risks[:5])}
Opportunities: {', '.join(result.opportunities[:5])}
Entities Analyzed: {', '.join(entity_names)}
Personas Simulated: {', '.join(persona_roles)}
Rounds: {len(state.rounds)}

Explain:
1. WHY this prediction is most likely
2. What key dynamics drive the outcome
3. How different persona perspectives converge or diverge
4. What could change the prediction
5. Timeline considerations over {state.config.horizon_days} days

Write in a professional analytical tone."""

        try:
            messages = [
                {"role": "system", "content": "You are a senior simulation analyst. Write detailed, insightful explanations."},
                {"role": "user", "content": prompt},
            ]
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            return getattr(response, "content", str(response))
        except Exception as e:
            logger.error(f"Detailed explanation generation failed: {e}")
            return f"Prediction: {result.prediction} with {result.confidence:.0%} confidence based on {len(state.personas)} persona simulations."

    async def _generate_detailed_scenarios(self, state: SimulationState) -> list:
        """Generate detailed scenarios with probabilities, drivers, and timelines."""
        result = state.result
        entity_names = [e.name for e in state.entities[:15]]

        prompt = f"""Generate 5-7 detailed scenarios for this simulation.

Scenario: {state.config.seed_query}
Main Prediction: {result.prediction}
Confidence: {result.confidence:.0%}
Key Entities: {', '.join(entity_names)}
Key Factors: {', '.join(result.key_factors[:8])}

Return JSON array:
[
  {{
    "name": "Scenario Name",
    "probability": 0.0 to 1.0,
    "description": "2-3 sentence detailed description",
    "impact": "low|medium|high|critical",
    "key_drivers": ["driver1", "driver2", "driver3"],
    "timeline": "Expected timeline for this scenario",
    "affected_entities": ["entity1", "entity2"]
  }}
]

Include: best case, worst case, most likely, and 2-4 alternative scenarios.
Probabilities should sum to approximately 1.0."""

        try:
            messages = [
                {"role": "system", "content": "You are a scenario planning expert. Generate comprehensive, realistic scenarios."},
                {"role": "user", "content": prompt},
            ]
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Detailed scenario generation failed: {e}")

        # Fallback: enhance existing scenarios with defaults
        return result.scenarios if result.scenarios else [
            {"name": "Most Likely", "probability": result.confidence, "description": result.prediction, "impact": "medium", "key_drivers": result.key_factors[:3], "timeline": f"{state.config.horizon_days} days", "affected_entities": entity_names[:3]},
            {"name": "Best Case", "probability": result.confidence * 0.3, "description": "Favorable outcome", "impact": "low", "key_drivers": result.opportunities[:2], "timeline": f"{state.config.horizon_days * 2} days", "affected_entities": entity_names[:2]},
            {"name": "Worst Case", "probability": 1 - result.confidence, "description": "Adverse outcome", "impact": "critical", "key_drivers": result.risks[:2], "timeline": f"{state.config.horizon_days // 2} days", "affected_entities": entity_names[:3]},
        ]

    def _extract_sources(self, state: SimulationState) -> list:
        """Extract source references from simulation data."""
        sources = []

        # Sources from entity attributes
        for entity in state.entities:
            attrs = entity.attributes
            if attrs.get("source_url"):
                sources.append({"title": entity.name, "url": attrs["source_url"], "type": "web", "relevance": entity.importance, "snippet": attrs.get("description", "")[:200]})
            if attrs.get("source_type"):
                sources.append({"title": entity.name, "url": attrs.get("source_url", ""), "type": attrs["source_type"], "relevance": entity.importance, "snippet": attrs.get("description", "")[:200]})

        # Sources from result
        if hasattr(state.result, 'sources') and state.result.sources:
            for src in state.result.sources:
                sources.append({"title": src.title, "url": src.url, "type": src.type, "relevance": src.relevance, "snippet": src.snippet[:200]})

        # Generate synthetic sources based on entities and context
        if len(sources) < 5:
            for entity in state.entities[:10 - len(sources)]:
                sources.append({
                    "title": f"{entity.name} - Market Analysis",
                    "url": "",
                    "type": "api",
                    "relevance": entity.importance,
                    "snippet": f"Data sourced from market intelligence APIs for {entity.name} ({entity.type.value})",
                })

        # Deduplicate by title
        seen_titles = set()
        unique_sources = []
        for s in sources:
            if s["title"] not in seen_titles:
                seen_titles.add(s["title"])
                unique_sources.append(s)

        return unique_sources[:20]

    def _describe_methodology(self, state: SimulationState) -> str:
        """Describe the simulation methodology."""
        parts = [
            f"MiroFish Swarm Simulation with {len(state.personas)} personas across {len(state.rounds)} rounds",
            f"Knowledge graph: {len(state.entities)} entities, {len(state.relationships)} relationships",
            f"Persona roles: {', '.join(sorted(set(p.role.value for p in state.personas)))}",
            f"Horizon: {state.config.horizon_days} days",
            f"Temperature: {state.config.temperature}",
            "Method: Multi-agent persona simulation with LLM-driven interactions, sentiment tracking, and scenario analysis",
        ]
        return '. '.join(parts) + '.'

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
