"""Graph Builder for MiroFish - Extracts entities and builds relationship graphs."""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from uuid import uuid4

from backend.mirofish.schemas import Entity, Relationship, EntityType, RelationshipType
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds entity-relationship graphs from scenario seeds."""
    
    def __init__(self):
        self.entity_patterns = {
            EntityType.COMPANY: [
                r'\b([A-Z][a-zA-Z\s]+(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Company|Technologies|Group))\b',
                r'\b(Apple|Google|Microsoft|Amazon|Tesla|Meta|Nvidia|Samsung|Sony|Intel)\b',
            ],
            EntityType.PRODUCT: [
                r'\b(iPhone|iPad|MacBook|Galaxy|Pixel|PlayStation|Xbox|Model [\w-]+)\b',
            ],
            EntityType.PERSON: [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:,\s*(?:CEO|CTO|President|Founder|Director))?)\b',
            ],
            EntityType.ORGANIZATION: [
                r'\b(FDA|EPA|EU Commission|WTO|UN|World Bank|IMF)\b',
                r'\b([A-Z]{2,}\s*(?:Association|Federation|Union|Council))\b',
            ],
            EntityType.MARKET: [
                r'\b(semiconductor|lithium|oil|steel|agriculture|automotive|tech|pharma)\s+market\b',
                r'\b(Asian|European|North American|Emerging)\s+market\b',
            ],
            EntityType.EVENT: [
                r'\b(supply chain disruption|tariff|sanction|recall|shortage|strike|pandemic)\b',
            ],
            EntityType.TREND: [
                r'\b(AI adoption|digital transformation|ESG|sustainability|inflation|deflation)\b',
            ],
            EntityType.POLICY: [
                r'\b(Infrastructure Act|Clean Energy|CHIPS Act|trade policy|regulation)\b',
            ],
        }
    
    async def build_graph(
        self,
        seed_query: str,
        context: Optional[str] = None,
        fast_mode: bool = True,
    ) -> tuple[List[Entity], List[Relationship]]:
        """Build entity-relationship graph from seed query.
        
        Args:
            seed_query: The scenario/prediction question
            context: Additional context (RAG results, etc.)
            fast_mode: Skip entity expansion for speed (default True)
            
        Returns:
            Tuple of (entities, relationships)
        """
        logger.info(f"Building graph for seed: {seed_query[:100]}... (fast_mode={fast_mode})")
        
        # Step 1: Run LLM entity extraction and pattern extraction in parallel
        llm_task = self._extract_entities_llm(seed_query, context)
        pattern_entities = self._extract_entities_patterns(seed_query)
        entities = await llm_task
        
        # Merge LLM and pattern entities (deduplicate by name)
        all_entities = self._merge_entities(entities, pattern_entities)
        
        # Step 2: Extract relationships (only one pass in fast mode)
        relationships = await self._extract_relationships_llm(all_entities, seed_query)
        
        # Step 3: Expand entities only if not in fast mode
        if not fast_mode and len(all_entities) >= 3:
            expanded_entities = await self._expand_entities_llm(all_entities, seed_query)
            all_entities = self._merge_entities(all_entities, expanded_entities)
            if len(expanded_entities) > 0:
                extra_rels = await self._extract_relationships_llm(all_entities[:30], seed_query)
                existing_pairs = {(r.source_id, r.target_id) for r in relationships}
                for r in extra_rels:
                    if (r.source_id, r.target_id) not in existing_pairs:
                        relationships.append(r)
                        existing_pairs.add((r.source_id, r.target_id))
        
        logger.info(f"Graph built: {len(all_entities)} entities, {len(relationships)} relationships")
        return all_entities, relationships
    
    async def _extract_entities_llm(
        self,
        seed_query: str,
        context: Optional[str],
    ) -> List[Entity]:
        """Use LLM to extract entities from seed."""
        
        prompt = f"""Extract ALL relevant entities from the following scenario/query for supply chain analysis. Be comprehensive - extract at least 15-25 entities.

Scenario: {seed_query}

{ f"Context: {context[:2000]}" if context else "" }

Extract entities in these categories:
- COMPANY: Companies, corporations, businesses, suppliers, distributors, competitors
- PRODUCT: Products, goods, materials, components, raw materials
- PERSON: Key individuals (executives, leaders, experts, regulators)
- ORGANIZATION: Organizations, associations, regulatory bodies, NGOs
- MARKET: Markets, sectors, industries, regional markets
- EVENT: Events, disruptions, incidents, crises, milestones
- TREND: Trends, patterns, movements, shifts, innovations
- POLICY: Policies, regulations, laws, trade agreements, tariffs

Return as JSON array:
[
  {{
    "name": "Entity Name",
    "type": "company|product|person|organization|market|event|trend|policy",
    "attributes": {{"key": "value"}},
    "importance": 0.9
  }}
]

Be thorough: include direct and indirect entities, upstream/downstream supply chain entities, competitors, regulators, and market forces."""

        try:
            messages = [
                {"role": "system", "content": "You are an entity extraction specialist. Extract key entities for supply chain scenario analysis."},
                {"role": "user", "content": prompt}
            ]
            
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))
            
            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                entities = []
                for item in data:
                    try:
                        entity_type = EntityType(item.get("type", "company").lower())
                    except ValueError:
                        entity_type = EntityType.COMPANY
                    
                    entities.append(Entity(
                        id=str(uuid4())[:8],
                        name=item.get("name", "Unknown"),
                        type=entity_type,
                        attributes=item.get("attributes", {}),
                        importance=item.get("importance", 0.5),
                    ))
                return entities
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
        
        return []
    
    def _extract_entities_patterns(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns."""
        entities = []
        seen = set()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    name = match.group(1) if match.groups() else match.group(0)
                    name = name.strip()
                    
                    if name and name.lower() not in seen:
                        seen.add(name.lower())
                        entities.append(Entity(
                            id=str(uuid4())[:8],
                            name=name,
                            type=entity_type,
                            importance=0.6,
                        ))
        
        return entities
    
    async def _extract_relationships_llm(
        self,
        entities: List[Entity],
        seed_query: str,
    ) -> List[Relationship]:
        """Use LLM to extract relationships between entities."""
        
        if len(entities) < 2:
            return []
        
        entity_list = "\n".join([f"- {e.name} ({e.type.value})" for e in entities[:30]])
        
        prompt = f"""Given these entities from the scenario "{seed_query[:100]}...":

{entity_list}

Identify relationships between them relevant to supply chain dynamics.

Relationship types:
- COMPETES_WITH: Competitive rivalry
- SUPPLIES: Supply relationship
- INFLUENCES: Market/influence relationship
- OPPOSES: Opposition/conflict
- SUPPORTS: Support/alliance
- CAUSED_BY: Causation
- LEADS_TO: Leads to outcome
- PART_OF: Component/part relationship

Return as JSON array:
[
  {{
    "source": "Entity Name",
    "target": "Entity Name",
    "type": "competes_with|supplies|influences|opposes|supports|caused_by|leads_to|part_of",
    "weight": 0.8,
    "description": "Brief description"
  }}
]

Focus on relationships that would matter in scenario prediction."""

        try:
            messages = [
                {"role": "system", "content": "You are a relationship extraction specialist. Identify how entities interact in supply chain scenarios."},
                {"role": "user", "content": prompt}
            ]
            
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))
            
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                relationships = []
                entity_map = {e.name.lower(): e.id for e in entities}
                
                for item in data:
                    source_name = item.get("source", "").lower()
                    target_name = item.get("target", "").lower()
                    
                    if source_name in entity_map and target_name in entity_map:
                        try:
                            rel_type = RelationshipType(item.get("type", "influences").lower())
                        except ValueError:
                            rel_type = RelationshipType.INFLUENCES
                        
                        relationships.append(Relationship(
                            source_id=entity_map[source_name],
                            target_id=entity_map[target_name],
                            type=rel_type,
                            weight=item.get("weight", 0.5),
                            description=item.get("description"),
                        ))
                
                return relationships
        except Exception as e:
            logger.error(f"LLM relationship extraction failed: {e}")
        
        return []
    
    async def _expand_entities_llm(
        self,
        entities: List[Entity],
        seed_query: str,
    ) -> List[Entity]:
        """Use LLM to derive secondary/related entities from the initial entity set."""
        if len(entities) < 3:
            return []

        entity_names = [f"- {e.name} ({e.type.value}, importance: {e.importance:.1f})" for e in entities[:20]]

        prompt = f"""Given these primary entities from the scenario "{seed_query[:150]}...":

{chr(10).join(entity_names)}

Identify ADDITIONAL secondary entities that are indirectly related but important for comprehensive supply chain analysis.
Think about: upstream suppliers, downstream customers, substitute products, regulatory bodies, industry associations, 
competing technologies, macro-economic factors, geographic regions, and logistical infrastructure.

Return as JSON array (max 15 entities):
[
  {{
    "name": "Entity Name",
    "type": "company|product|person|organization|market|event|trend|policy",
    "attributes": {{"key": "value"}},
    "importance": 0.7
  }}
]

Only include entities NOT already in the list above. Focus on entities that create hidden dependencies or blind spots."""

        try:
            messages = [
                {"role": "system", "content": "You are a supply chain analysis expert. Identify hidden dependencies and secondary entities."},
                {"role": "user", "content": prompt}
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                expanded = []
                for item in data:
                    try:
                        entity_type = EntityType(item.get("type", "company").lower())
                    except ValueError:
                        entity_type = EntityType.COMPANY

                    expanded.append(Entity(
                        id=str(uuid4())[:8],
                        name=item.get("name", "Unknown"),
                        type=entity_type,
                        attributes=item.get("attributes", {}),
                        importance=item.get("importance", 0.5),
                    ))
                return expanded
        except Exception as e:
            logger.error(f"LLM entity expansion failed: {e}")

        return []

    def _merge_entities(
        self,
        llm_entities: List[Entity],
        pattern_entities: List[Entity],
    ) -> List[Entity]:
        """Merge entity lists, deduplicating by name."""
        seen = {e.name.lower(): e for e in llm_entities}
        
        for entity in pattern_entities:
            key = entity.name.lower()
            if key not in seen:
                seen[key] = entity
            else:
                # Boost importance if found by both methods
                seen[key].importance = min(1.0, seen[key].importance + 0.1)
        
        return list(seen.values())
