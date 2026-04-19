"""Persona Generator for MiroFish - Creates simulation agent personas from entities."""

import logging
import json
import re
from typing import List, Optional, Dict
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
        """Generate personas for simulation. Supports 50+ personas with batch generation."""
        logger.info(f"Generating up to {config.num_personas} personas...")

        scored_entities = self._score_entities(entities, relationships)

        # Distribute roles evenly across all persona slots
        all_roles = list(PersonaRole)
        role_distribution = self._distribute_roles(config.num_personas, all_roles, scored_entities)

        personas: List[Persona] = []

        # Generate ALL personas in batch (1-2 LLM calls instead of 50 individual calls)
        batch_personas = await self._batch_generate_personas(
            config.num_personas, scored_entities, relationships, config, role_distribution
        )
        personas.extend(batch_personas)

        # Ensure minimum role coverage
        role_coverage = {p.role for p in personas}
        for required_role in [PersonaRole.ANALYST, PersonaRole.CUSTOMER, PersonaRole.INVESTOR,
                              PersonaRole.REGULATOR, PersonaRole.MEDIA, PersonaRole.COMPETITOR,
                              PersonaRole.SUPPLIER, PersonaRole.EXPERT]:
            if required_role not in role_coverage:
                persona = self._create_fallback_persona(required_role, config)
                personas.append(persona)

        logger.info(f"Generated {len(personas)} personas across {len({p.role for p in personas})} roles")
        return personas

    def _distribute_roles(
        self,
        num_personas: int,
        all_roles: List[PersonaRole],
        entities: List[Entity],
    ) -> List[PersonaRole]:
        """Distribute roles evenly, weighted by entity types present."""
        distribution: List[PersonaRole] = []
        
        # Weight roles by entity type presence
        entity_types_present = {e.type for e in entities}
        role_weights: Dict[PersonaRole, float] = {}
        for role in all_roles:
            weight = 1.0
            for etype, preferred_roles in self.ROLE_WEIGHTS.items():
                if etype in entity_types_present and role in preferred_roles:
                    weight += 0.5 * (preferred_roles.index(role) == 0)
            role_weights[role] = weight
        
        total_weight = sum(role_weights.values())
        
        for role in all_roles:
            count = max(1, round(num_personas * role_weights[role] / total_weight))
            distribution.extend([role] * count)
        
        # Trim or pad to exact count
        distribution = distribution[:num_personas]
        while len(distribution) < num_personas:
            distribution.append(all_roles[len(distribution) % len(all_roles)])
        
        return distribution

    def _create_fallback_persona(self, role: PersonaRole, config: SimulationConfig) -> Persona:
        """Create a fallback persona without LLM."""
        role_names = {
            PersonaRole.COMPETITOR: "Competitive Rival",
            PersonaRole.CUSTOMER: "Customer Advocate",
            PersonaRole.MEDIA: "Media Correspondent",
            PersonaRole.REGULATOR: "Regulatory Official",
            PersonaRole.INVESTOR: "Investment Analyst",
            PersonaRole.ANALYST: "Industry Analyst",
            PersonaRole.SUPPLIER: "Supply Chain Partner",
            PersonaRole.EXPERT: "Domain Expert",
        }
        role_traits = {
            PersonaRole.COMPETITOR: ["aggressive", "market-focused", "opportunistic"],
            PersonaRole.CUSTOMER: ["price-sensitive", "quality-focused", "brand-aware"],
            PersonaRole.MEDIA: ["narrative-driven", "public-focused", "sensational"],
            PersonaRole.REGULATOR: ["compliance-focused", "cautious", "public-interest"],
            PersonaRole.INVESTOR: ["return-focused", "risk-aware", "data-driven"],
            PersonaRole.ANALYST: ["data-driven", "objective", "cautious"],
            PersonaRole.SUPPLIER: ["relationship-focused", "capacity-aware", "pricing-sensitive"],
            PersonaRole.EXPERT: ["technical", "evidence-based", "forward-looking"],
        }
        return Persona(
            id=str(uuid4())[:8],
            name=role_names.get(role, role.value.title()),
            role=role,
            system_prompt=self.ROLE_PROMPTS[role],
            traits=role_traits.get(role, ["analytical"]),
            goals=["evaluate scenario impact"],
            memory=[f"Scenario: {config.seed_query[:200]}"],
            position={"optimism": 0.0, "risk_tolerance": 0.0},
        )

    async def _batch_generate_personas(
        self,
        count: int,
        entities: List[Entity],
        relationships: List[Relationship],
        config: SimulationConfig,
        roles: List[PersonaRole],
    ) -> List[Persona]:
        """Generate multiple personas in a single LLM call for efficiency."""
        entity_names = [e.name for e in entities[:15]]
        roles_needed = roles[:count] if roles else [PersonaRole.ANALYST] * count

        prompt = f"""Create {count} diverse personas for supply chain simulation.

Scenario: {config.seed_query}
Related Entities: {', '.join(entity_names)}

Roles needed: {', '.join(set(r.value for r in roles_needed))}

Generate a JSON array of {count} personas:
[
  {{
    "name": "Realistic professional name",
    "role": "competitor|customer|media|regulator|investor|analyst|supplier|expert",
    "traits": ["trait1", "trait2", "trait3"],
    "goals": ["goal1", "goal2"],
    "position": {{"optimism": -1.0 to 1.0, "risk_tolerance": -1.0 to 1.0, "influence": 0.0 to 1.0}}
  }}
]

Ensure diversity in perspectives, backgrounds, and positions. Make each persona unique and realistic."""

        try:
            messages = [
                {"role": "system", "content": "You are a persona designer for AI simulations. Create diverse, realistic personas in bulk."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                personas = []
                for i, item in enumerate(data[:count]):
                    try:
                        role = PersonaRole(item.get("role", roles_needed[i].value if i < len(roles_needed) else "analyst").lower())
                    except (ValueError, IndexError):
                        role = roles_needed[i] if i < len(roles_needed) else PersonaRole.ANALYST

                    personas.append(Persona(
                        id=str(uuid4())[:8],
                        name=item.get("name", f"{role.value}_{i}"),
                        role=role,
                        system_prompt=self.ROLE_PROMPTS[role],
                        traits=item.get("traits", ["analytical"]),
                        goals=item.get("goals", ["evaluate scenario"]),
                        memory=[f"Scenario: {config.seed_query[:200]}"],
                        position=item.get("position", {"optimism": 0.0, "risk_tolerance": 0.0}),
                    ))
                return personas
        except Exception as e:
            logger.error(f"Batch persona generation failed: {e}")

        # Fallback: create without LLM
        return [self._create_fallback_persona(
            roles_needed[i] if i < len(roles_needed) else PersonaRole.ANALYST, config
        ) for i in range(count)]

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
