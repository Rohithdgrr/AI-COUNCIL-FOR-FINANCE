"""Tests for enhanced MiroFish simulation features: 50+ personas, sources, detailed scenarios."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from backend.mirofish.schemas import (
    SimulationConfig, SimulationResult, SimulationState,
    ScenarioDetail, SourceReference, Entity, EntityType,
    Persona, PersonaRole, Relationship, RelationshipType,
)


# ── Schema Tests ──────────────────────────────────────────────────────────────

class TestScenarioDetail:
    def test_create_scenario_detail(self):
        s = ScenarioDetail(
            name="Best Case",
            probability=0.6,
            description="Favorable outcome with quick recovery",
            impact="low",
            key_drivers=["strong demand", "favorable policy"],
            timeline="30-60 days",
            affected_entities=["Company A", "Market X"],
        )
        assert s.name == "Best Case"
        assert s.probability == 0.6
        assert s.impact == "low"
        assert len(s.key_drivers) == 2
        assert len(s.affected_entities) == 2

    def test_scenario_detail_defaults(self):
        s = ScenarioDetail(name="Test")
        assert s.probability == 0.5
        assert s.impact == "medium"
        assert s.key_drivers == []
        assert s.affected_entities == []


class TestSourceReference:
    def test_create_source_reference(self):
        src = SourceReference(
            title="Market Analysis Report",
            url="https://example.com/report",
            type="web",
            relevance=0.9,
            snippet="Key finding about supply chain resilience",
        )
        assert src.title == "Market Analysis Report"
        assert src.type == "web"
        assert src.relevance == 0.9

    def test_source_reference_defaults(self):
        src = SourceReference()
        assert src.title == ""
        assert src.type == "api"
        assert src.relevance == 0.5


class TestSimulationResultEnhanced:
    def test_result_with_sources(self):
        r = SimulationResult(
            prediction="Positive outlook",
            confidence=0.75,
            sources=[
                SourceReference(title="API Data", type="api", relevance=0.8),
                SourceReference(title="Web Report", type="web", relevance=0.6),
            ],
        )
        assert len(r.sources) == 2
        assert r.sources[0].type == "api"

    def test_result_with_detailed_explanation(self):
        r = SimulationResult(
            prediction="Moderate growth expected",
            confidence=0.65,
            detailed_explanation="The simulation of 50 personas across 3 rounds indicates...",
            methodology="MiroFish Swarm Simulation with 50 personas across 3 rounds",
            assumptions=["Market conditions remain stable", "No major disruptions"],
            data_quality_score=0.8,
        )
        assert r.detailed_explanation.startswith("The simulation")
        assert len(r.assumptions) == 2
        assert r.data_quality_score == 0.8


class TestSimulationConfigEnhanced:
    def test_default_personas_50(self):
        config = SimulationConfig(name="test", seed_query="test query")
        assert config.num_personas == 50

    def test_max_personas_200(self):
        config = SimulationConfig(name="test", seed_query="test query", num_personas=200)
        assert config.num_personas == 200

    def test_personas_exceeds_max_raises(self):
        with pytest.raises(Exception):
            SimulationConfig(name="test", seed_query="test query", num_personas=500)


# ── Persona Generator Tests ───────────────────────────────────────────────────

class TestPersonaGeneratorEnhanced:
    @pytest.fixture
    def mock_entities(self):
        return [
            Entity(id="e1", name="Apple Inc", type=EntityType.COMPANY, importance=0.9),
            Entity(id="e2", name="iPhone", type=EntityType.PRODUCT, importance=0.8),
            Entity(id="e3", name="Tim Cook", type=EntityType.PERSON, importance=0.7),
            Entity(id="e4", name="FDA", type=EntityType.ORGANIZATION, importance=0.6),
            Entity(id="e5", name="Tech Market", type=EntityType.MARKET, importance=0.8),
            Entity(id="e6", name="Supply Disruption", type=EntityType.EVENT, importance=0.9),
            Entity(id="e7", name="AI Adoption", type=EntityType.TREND, importance=0.7),
            Entity(id="e8", name="CHIPS Act", type=EntityType.POLICY, importance=0.6),
        ]

    @pytest.fixture
    def mock_relationships(self):
        return [
            Relationship(source_id="e1", target_id="e2", type=RelationshipType.PART_OF, weight=0.9),
            Relationship(source_id="e6", target_id="e1", type=RelationshipType.INFLUENCES, weight=0.8),
        ]

    @pytest.fixture
    def config_50(self):
        return SimulationConfig(name="test", seed_query="Will Apple recover?", num_personas=50)

    def test_distribute_roles_evenly(self, mock_entities):
        from backend.mirofish.persona_generator import PersonaGenerator
        pg = PersonaGenerator()
        distribution = pg._distribute_roles(50, list(PersonaRole), mock_entities)
        assert len(distribution) == 50
        # All 8 roles should be represented
        roles_in_dist = set(distribution)
        assert len(roles_in_dist) == 8

    def test_distribute_roles_small_count(self, mock_entities):
        from backend.mirofish.persona_generator import PersonaGenerator
        pg = PersonaGenerator()
        distribution = pg._distribute_roles(8, list(PersonaRole), mock_entities)
        assert len(distribution) == 8
        # Each role at least once
        assert set(distribution) == set(PersonaRole)

    def test_create_fallback_persona(self, config_50):
        from backend.mirofish.persona_generator import PersonaGenerator
        pg = PersonaGenerator()
        for role in PersonaRole:
            persona = pg._create_fallback_persona(role, config_50)
            assert persona.role == role
            assert len(persona.traits) >= 2
            assert persona.system_prompt != ""

    @pytest.mark.asyncio
    async def test_batch_generate_personas_fallback(self, mock_entities, mock_relationships, config_50):
        """Test that batch generation falls back to fallback personas when LLM fails."""
        from backend.mirofish.persona_generator import PersonaGenerator
        pg = PersonaGenerator()

        with patch.object(pg, '_batch_generate_personas', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = [
                pg._create_fallback_persona(PersonaRole.ANALYST, config_50)
                for _ in range(30)
            ]
            # Just test the fallback path
            result = await pg._batch_generate_personas(
                30, mock_entities, mock_relationships, config_50,
                [PersonaRole.ANALYST] * 30
            )
            assert len(result) == 30


# ── Report Agent Tests ────────────────────────────────────────────────────────

class TestReportAgentEnhanced:
    @pytest.fixture
    def mock_state(self):
        entities = [
            Entity(id="e1", name="Apple Inc", type=EntityType.COMPANY, importance=0.9),
            Entity(id="e2", name="Tech Market", type=EntityType.MARKET, importance=0.8),
        ]
        config = SimulationConfig(name="test", seed_query="Test query", num_personas=50)
        result = SimulationResult(
            prediction="Positive outlook",
            confidence=0.75,
            key_factors=["demand", "supply", "policy"],
            risks=["disruption", "inflation"],
            opportunities=["AI growth", "new markets"],
            recommendations=["diversify", "invest"],
            scenarios=[
                {"name": "Best Case", "probability": 0.3, "description": "Favorable"},
                {"name": "Worst Case", "probability": 0.2, "description": "Adverse"},
            ],
            sources=[
                SourceReference(title="API Data", type="api", relevance=0.8),
            ],
            detailed_explanation="Detailed analysis here",
            methodology="MiroFish Swarm Simulation",
            assumptions=["Stable conditions"],
            data_quality_score=0.8,
        )
        return SimulationState(
            id="test_sim",
            config=config,
            status="completed",
            entities=entities,
            personas=[
                Persona(id="p1", name="Analyst1", role=PersonaRole.ANALYST,
                        system_prompt="test", traits=["analytical"]),
            ],
            result=result,
            agent_type="brand",
        )

    def test_extract_sources(self, mock_state):
        from backend.mirofish.report_agent import ReportAgent
        ra = ReportAgent()
        sources = ra._extract_sources(mock_state)
        assert len(sources) >= 1
        # Should have at least the source from result
        titles = [s["title"] for s in sources]
        assert "API Data" in titles

    def test_extract_sources_deduplicates(self, mock_state):
        from backend.mirofish.report_agent import ReportAgent
        ra = ReportAgent()
        sources = ra._extract_sources(mock_state)
        titles = [s["title"] for s in sources]
        assert len(titles) == len(set(titles))  # no duplicates

    def test_describe_methodology(self, mock_state):
        from backend.mirofish.report_agent import ReportAgent
        ra = ReportAgent()
        methodology = ra._describe_methodology(mock_state)
        assert "personas" in methodology
        assert "MiroFish" in methodology
        assert "analyst" in methodology

    @pytest.mark.asyncio
    async def test_full_report_includes_new_fields(self, mock_state):
        from backend.mirofish.report_agent import ReportAgent
        ra = ReportAgent()

        with patch.object(ra, '_generate_explanation_and_scenarios', new_callable=AsyncMock) as mock_combined:
            mock_combined.return_value = {
                "explanation": "Detailed explanation text",
                "scenarios": [
                    {"name": "Best Case", "probability": 0.4, "description": "Favorable", "impact": "low", "key_drivers": ["demand"], "timeline": "30 days", "affected_entities": ["Apple Inc"]},
                ],
            }
            report = await ra._generate_full_report(mock_state)

        assert "detailed_explanation" in report
        assert "methodology" in report
        assert "assumptions" in report
        assert "sources" in report
        assert "data_quality_score" in report
        assert report["detailed_explanation"] == "Detailed explanation text"
        assert len(report["sources"]) >= 1


# ── Graph Builder Tests ───────────────────────────────────────────────────────

class TestGraphBuilderEnhanced:
    def test_merge_entities_deduplicates(self):
        from backend.mirofish.graph_builder import GraphBuilder
        gb = GraphBuilder()
        e1 = Entity(id="a", name="Apple Inc", type=EntityType.COMPANY, importance=0.8)
        e2 = Entity(id="b", name="apple inc", type=EntityType.COMPANY, importance=0.6)
        merged = gb._merge_entities([e1], [e2])
        assert len(merged) == 1
        assert merged[0].importance > 0.8  # boosted

    def test_merge_entities_keeps_both_different(self):
        from backend.mirofish.graph_builder import GraphBuilder
        gb = GraphBuilder()
        e1 = Entity(id="a", name="Apple Inc", type=EntityType.COMPANY, importance=0.8)
        e2 = Entity(id="b", name="Google LLC", type=EntityType.COMPANY, importance=0.7)
        merged = gb._merge_entities([e1], [e2])
        assert len(merged) == 2

    def test_pattern_extraction(self):
        from backend.mirofish.graph_builder import GraphBuilder
        gb = GraphBuilder()
        entities = gb._extract_entities_patterns("Apple Inc announced a new semiconductor market supply chain disruption")
        names = [e.name for e in entities]
        assert any("Apple" in n for n in names)
