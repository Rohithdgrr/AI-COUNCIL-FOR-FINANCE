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
    ) -> tuple[List[Entity], List[Relationship]]:
        """Build entity-relationship graph from seed query.
        
        Args:
            seed_query: The scenario/prediction question
            context: Additional context (RAG results, etc.)
            
        Returns:
            Tuple of (entities, relationships)
        """
        logger.info(f"Building graph for seed: {seed_query[:100]}...")
        
        # Step 1: Extract entities using LLM
        entities = await self._extract_entities_llm(seed_query, context)
        
        # Step 2: Extract relationships
        relationships = await self._extract_relationships_llm(entities, seed_query)
        
        # Step 3: Add pattern-based entities as supplement
        pattern_entities = self._extract_entities_patterns(seed_query)
        
        # Merge LLM and pattern entities (deduplicate by name)
        all_entities = self._merge_entities(entities, pattern_entities)
        
        logger.info(f"Graph built: {len(all_entities)} entities, {len(relationships)} relationships")
        return all_entities, relationships
    
    async def _extract_entities_llm(
        self,
        seed_query: str,
        context: Optional[str],
    ) -> List[Entity]:
        """Use LLM to extract entities from seed."""
        
        prompt = f"""Extract all relevant entities from the following scenario/query for supply chain analysis.

Scenario: {seed_query}

{ f"Context: {context[:2000]}" if context else "" }

Extract entities in these categories:
- COMPANY: Companies, corporations, businesses
- PRODUCT: Products, goods, materials, components
- PERSON: Key individuals (executives, leaders, experts)
- ORGANIZATION: Organizations, associations, regulatory bodies
- MARKET: Markets, sectors, industries
- EVENT: Events, disruptions, incidents
- TREND: Trends, patterns, movements
- POLICY: Policies, regulations, laws

Return as JSON array:
[
  {{
    "name": "Entity Name",
    "type": "company|product|person|organization|market|event|trend|policy",
    "attributes": {{"key": "value"}},
    "importance": 0.9
  }}
]

Include only entities relevant to supply chain and business impact analysis."""

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
        
        entity_list = "\n".join([f"- {e.name} ({e.type.value})" for e in entities[:15]])
        
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
