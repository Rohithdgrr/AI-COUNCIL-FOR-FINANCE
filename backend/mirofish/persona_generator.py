"""Persona Generator for MiroFish - Creates simulation agent personas from entities."""

import logging
import json
import re
from typing import List, Optional
from uuid import uuid4

from backend.mirofish.schemas import (
    Entity, Relationship, Persona, PersonaRole, SimulationConfig, EntityType
)
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """Generates realistic personas for simulation based on entities."""

    ROLE_PROMPTS = {
        PersonaRole.COMPETITOR: "You are a competitive rival. Be aggressive, focus on market share, pricing, and competitive advantages.",
        PersonaRole.CUSTOMER: "You are a customer/user. Focus on price sensitivity, quality concerns, brand loyalty, and switching costs.",
        PersonaRole.MEDIA: "You are a media analyst/journalist. Focus on narrative, public perception, headline potential, and story angles.",
        PersonaRole.REGULATOR: "You are a regulatory/government official. Focus on compliance, public interest, precedent, and political implications.",
        PersonaRole.INVESTOR: "You are an investor/analyst. Focus on financial impact, stock price, ROI, risk-adjusted returns.",
        PersonaRole.ANALYST: "You are an industry analyst. Focus on trends, data, historical patterns, and expert insights.",
        PersonaRole.SUPPLIER: "You are a supplier/vendor. Focus on supply relationships, pricing power, alternatives, and contract terms.",
        PersonaRole.EXPERT: "You are a domain expert. Focus on technical feasibility, industry best practices, and specialized knowledge.",
    }

    ROLE_WEIGHTS = {
        EntityType.COMPANY: [PersonaRole.COMPETITOR, PersonaRole.INVESTOR, PersonaRole.ANALYST],
        EntityType.PRODUCT: [PersonaRole.CUSTOMER, PersonaRole.ANALYST, PersonaRole.EXPERT],
        EntityType.PERSON: [PersonaRole.MEDIA, PersonaRole.ANALYST, PersonaRole.EXPERT],
        EntityType.ORGANIZATION: [PersonaRole.REGULATOR, PersonaRole.ANALYST, PersonaRole.MEDIA],
        EntityType.MARKET: [PersonaRole.ANALYST, PersonaRole.INVESTOR, PersonaRole.EXPERT],
        EntityType.EVENT: [PersonaRole.MEDIA, PersonaRole.ANALYST, PersonaRole.REGULATOR],
        EntityType.TREND: [PersonaRole.ANALYST, PersonaRole.EXPERT, PersonaRole.INVESTOR],
        EntityType.POLICY: [PersonaRole.REGULATOR, PersonaRole.ANALYST, PersonaRole.EXPERT],
    }

    async def generate_personas(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        config: SimulationConfig,
    ) -> List[Persona]:
        """Generate personas for simulation."""
        logger.info(f"Generating up to {config.num_personas} personas...")

        scored_entities = self._score_entities(entities, relationships)
        selected_entities = scored_entities[:config.num_personas]

        personas: List[Persona] = []
        for entity in selected_entities:
            possible_roles = self.ROLE_WEIGHTS.get(entity.type, [PersonaRole.ANALYST])
            role = possible_roles[0]

            persona = await self._create_persona(entity, role, config, relationships)
            if persona:
                personas.append(persona)

            if len(personas) >= config.num_personas:
                break

        # Always include at least one analyst and one customer perspective
        role_coverage = {p.role for p in personas}
        if PersonaRole.ANALYST not in role_coverage:
            analyst = Persona(
                id=str(uuid4())[:8],
                name="Industry Analyst",
                role=PersonaRole.ANALYST,
                system_prompt=self.ROLE_PROMPTS[PersonaRole.ANALYST],
                traits=["data-driven", "objective", "cautious"],
                goals=["identify trends", "validate claims with data"],
                memory=[f"Scenario: {config.seed_query[:200]}"],
                position={"optimism": 0.0, "risk_tolerance": 0.0},
            )
            personas.append(analyst)

        if PersonaRole.CUSTOMER not in role_coverage:
            customer = Persona(
                id=str(uuid4())[:8],
                name="Customer Representative",
                role=PersonaRole.CUSTOMER,
                system_prompt=self.ROLE_PROMPTS[PersonaRole.CUSTOMER],
                traits=["price-sensitive", "quality-focused", "brand-aware"],
                goals=["evaluate value proposition", "assess switching costs"],
                memory=[f"Scenario: {config.seed_query[:200]}"],
                position={"optimism": 0.2, "risk_tolerance": -0.3},
            )
            personas.append(customer)

        logger.info(f"Generated {len(personas)} personas")
        return personas

    def _score_entities(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
    ) -> List[Entity]:
        """Score and sort entities by importance for persona generation."""
        rel_counts: dict[str, int] = {}
        for rel in relationships:
            rel_counts[rel.source_id] = rel_counts.get(rel.source_id, 0) + 1
            rel_counts[rel.target_id] = rel_counts.get(rel.target_id, 0) + 1

        scored = []
        for entity in entities:
            score = entity.importance
            score += min(0.3, rel_counts.get(entity.id, 0) * 0.1)
            if entity.type in [EntityType.COMPANY, EntityType.PERSON]:
                score += 0.2
            scored.append((score, entity))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored]

    async def _create_persona(
        self,
        entity: Entity,
        role: PersonaRole,
        config: SimulationConfig,
        relationships: List[Relationship],
    ) -> Optional[Persona]:
        """Create a single persona using LLM."""
        related = []
        for rel in relationships:
            if rel.source_id == entity.id:
                related.append(f"{rel.type.value} -> {rel.target_id}")
            elif rel.target_id == entity.id:
                related.append(f"<- {rel.type.value} {rel.source_id}")

        related_str = "\n".join(related[:5]) if related else "None identified"

        prompt = f"""Create a detailed persona for supply chain simulation.

Entity: {entity.name} (Type: {entity.type.value})
Role in Simulation: {role.value}
Scenario: {config.seed_query}
Related Relationships:
{related_str}

Generate a persona with these fields as JSON:
{{
  "name": "Persona name (realistic, professional)",
  "traits": ["trait1", "trait2", "trait3"],
  "goals": ["goal1", "goal2"],
  "position": {{"optimism": -1.0 to 1.0, "risk_tolerance": -1.0 to 1.0, "influence": 0.0 to 1.0}}
}}

Make the persona realistic and relevant to the supply chain scenario."""

        try:
            messages = [
                {"role": "system", "content": "You are a persona designer for AI simulations. Create realistic, diverse personas."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return Persona(
                    id=str(uuid4())[:8],
                    name=data.get("name", f"{role.value}_{entity.name}"),
                    role=role,
                    entity_id=entity.id,
                    system_prompt=self.ROLE_PROMPTS[role],
                    traits=data.get("traits", ["analytical"]),
                    goals=data.get("goals", ["evaluate scenario"]),
                    memory=[f"Scenario: {config.seed_query[:200]}"],
                    position=data.get("position", {"optimism": 0.0, "risk_tolerance": 0.0}),
                )
        except Exception as e:
            logger.error(f"LLM persona generation failed for {entity.name}: {e}")

        # Fallback: create persona without LLM
        return Persona(
            id=str(uuid4())[:8],
            name=f"{role.value}_{entity.name}",
            role=role,
            entity_id=entity.id,
            system_prompt=self.ROLE_PROMPTS[role],
            traits=["analytical", "cautious"],
            goals=["evaluate scenario impact"],
            memory=[f"Scenario: {config.seed_query[:200]}"],
            position={"optimism": 0.0, "risk_tolerance": 0.0},
        )
