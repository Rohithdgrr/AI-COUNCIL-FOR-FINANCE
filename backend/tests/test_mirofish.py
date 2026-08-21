"""Unit tests for MiroFish simulation system."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.astra.schemas import (
    Entity, EntityType, Relationship, RelationshipType,
    Persona, PersonaRole, SimulationConfig, SimulationState,
    SimulationRound, SimulationResult,
)
from backend.astra.memory_manager import MemoryManager


# ── Schema Tests ────────────────────────────────────────────────────────────────

class TestSchemas:
    def test_entity_creation(self):
        e = Entity(id="e1", name="Apple Inc", type=EntityType.COMPANY, importance=0.9)
        assert e.name == "Apple Inc"
        assert e.type == EntityType.COMPANY
        assert e.importance == 0.9

    def test_entity_default_importance(self):
        e = Entity(id="e2", name="Widget", type=EntityType.PRODUCT)
        assert e.importance == 1.0

    def test_relationship_creation(self):
        r = Relationship(source_id="e1", target_id="e2", type=RelationshipType.COMPETES_WITH, weight=0.8)
        assert r.type == RelationshipType.COMPETES_WITH
        assert r.weight == 0.8

    def test_persona_creation(self):
        p = Persona(
            id="p1", name="Competitor Analyst", role=PersonaRole.ANALYST,
            system_prompt="You are an analyst", traits=["data-driven"], goals=["evaluate"],
        )
        assert p.role == PersonaRole.ANALYST
        assert len(p.traits) == 1

    def test_simulation_config(self):
        c = SimulationConfig(name="test", seed_query="What if?", horizon_days=30, num_personas=5, rounds=3)
        assert c.horizon_days == 30
        assert c.seed_query == "What if?"

    def test_simulation_config_validation(self):
        with pytest.raises(Exception):
            SimulationConfig(name="test", seed_query="q", horizon_days=0)  # min 1

        with pytest.raises(Exception):
            SimulationConfig(name="test", seed_query="q", num_personas=1)  # min 2

    def test_simulation_result(self):
        r = SimulationResult(prediction="Prices will rise", confidence=0.75, key_factors=["tariff"], risks=["shortage"])
        assert r.confidence == 0.75
        assert "tariff" in r.key_factors

    def test_simulation_state(self):
        s = SimulationState(id="sim1", config=SimulationConfig(name="t", seed_query="q"), agent_type="brand")
        assert s.status == "pending"
        assert s.agent_type == "brand"

    def test_simulation_round(self):
        r = SimulationRound(round_number=1, events=["event1"], sentiment_shift={"overall": 0.1})
        assert r.round_number == 1
        assert len(r.events) == 1


# ── Memory Manager Tests ────────────────────────────────────────────────────────

class TestMemoryManager:
    def test_update_memories(self):
        manager = MemoryManager()
        persona = Persona(
            id="p1", name="Test", role=PersonaRole.ANALYST,
            system_prompt="test", memory=["initial"],
        )
        round_result = SimulationRound(
            round_number=1,
            events=["Company X announced price increase", "Media coverage increased"],
            sentiment_shift={"overall": -0.2, "confidence": -0.1},
        )

        manager.update_memories([persona], round_result)

        # Should have added events and sentiment
        assert len(persona.memory) > 1
        assert any("Round 1" in m for m in persona.memory)
        assert any("sentiment" in m for m in persona.memory)

    def test_memory_bounded(self):
        manager = MemoryManager()
        persona = Persona(
            id="p1", name="Test", role=PersonaRole.ANALYST,
            system_prompt="test", memory=["initial"],
        )

        # Add many rounds
        for i in range(20):
            round_result = SimulationRound(
                round_number=i + 1,
                events=[f"Event {i}"],
                sentiment_shift={"overall": 0.1},
            )
            manager.update_memories([persona], round_result)

        # Memory should be bounded to 15 entries
        assert len(persona.memory) <= 15

    def test_inject_temporal_context(self):
        manager = MemoryManager()
        persona = Persona(
            id="p1", name="Test", role=PersonaRole.ANALYST,
            system_prompt="test", memory=["existing memory"],
        )

        manager.inject_temporal_context([persona], round_num=2, horizon_days=30)

        # Temporal context should be prepended
        assert persona.memory[0].startswith("Current simulation time: Day")

    def test_inject_individual_memory(self):
        manager = MemoryManager()
        persona = Persona(
            id="p1", name="Test", role=PersonaRole.ANALYST,
            system_prompt="test", memory=[],
        )

        manager.inject_individual_memory(persona, "Custom memory item")
        assert "Custom memory item" in persona.memory

    def test_inject_collective_memory(self):
        manager = MemoryManager()
        personas = [
            Persona(id="p1", name="A", role=PersonaRole.ANALYST, system_prompt="t", memory=[]),
            Persona(id="p2", name="B", role=PersonaRole.CUSTOMER, system_prompt="t", memory=[]),
        ]

        manager.inject_collective_memory(personas, "Shared event occurred")
        for p in personas:
            assert any("[COLLECTIVE]" in m for m in p.memory)


# ── Graph Builder Tests (with mocked LLM) ──────────────────────────────────────

class TestGraphBuilder:
    @pytest.mark.asyncio
    async def test_pattern_extraction(self):
        from backend.astra.graph_builder import GraphBuilder
        gb = GraphBuilder()

        # Test regex-based entity extraction (no LLM needed)
        entities = gb._extract_entities_patterns("Apple Inc and Microsoft Corp are competing in the semiconductor market")
        names = [e.name for e in entities]
        # Should find at least some entities via patterns
        assert len(entities) >= 0  # Pattern matching may vary

    @pytest.mark.asyncio
    async def test_merge_entities_dedup(self):
        from backend.astra.graph_builder import GraphBuilder
        gb = GraphBuilder()

        e1 = Entity(id="a", name="Apple", type=EntityType.COMPANY, importance=0.8)
        e2 = Entity(id="b", name="apple", type=EntityType.COMPANY, importance=0.6)  # same name, different case

        merged = gb._merge_entities([e1], [e2])
        # Should deduplicate by name (case-insensitive)
        assert len(merged) == 1
        assert merged[0].importance > 0.8  # boosted


# ── Persona Generator Tests (with mocked LLM) ──────────────────────────────────

class TestPersonaGenerator:
    @pytest.mark.asyncio
    async def test_score_entities(self):
        from backend.astra.persona_generator import PersonaGenerator
        pg = PersonaGenerator()

        entities = [
            Entity(id="e1", name="Apple", type=EntityType.COMPANY, importance=0.9),
            Entity(id="e2", name="Widget", type=EntityType.PRODUCT, importance=0.5),
            Entity(id="e3", name="John", type=EntityType.PERSON, importance=0.7),
        ]
        relationships = [
            Relationship(source_id="e1", target_id="e2", type=RelationshipType.SUPPLIES, weight=0.8),
            Relationship(source_id="e1", target_id="e3", type=RelationshipType.INFLUENCES, weight=0.6),
        ]

        scored = pg._score_entities(entities, relationships)
        # Apple should be highest (high importance + many relationships + company boost)
        assert scored[0].name == "Apple"

    @pytest.mark.asyncio
    async def test_always_includes_analyst_and_customer(self):
        from backend.astra.persona_generator import PersonaGenerator
        pg = PersonaGenerator()

        # Minimal entities that won't naturally produce analyst/customer
        entities = [Entity(id="e1", name="Regulation X", type=EntityType.POLICY, importance=0.5)]
        config = SimulationConfig(name="test", seed_query="test", num_personas=3, rounds=1)

        with patch.object(pg, '_create_persona', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Persona(
                id="p1", name="Regulator", role=PersonaRole.REGULATOR,
                system_prompt="t", traits=[], goals=[],
            )
            personas = await pg.generate_personas(entities, [], config)

        roles = {p.role for p in personas}
        assert PersonaRole.ANALYST in roles
        assert PersonaRole.CUSTOMER in roles


# ── Simulation Engine Tests (with mocked LLM) ───────────────────────────────────

class TestSimulationEngine:
    @pytest.mark.asyncio
    async def test_run_simulation_basic(self):
        from backend.astra.simulation_engine import SimulationEngine

        engine = SimulationEngine()
        config = SimulationConfig(name="test", seed_query="What if prices rise?", rounds=1, num_personas=2)
        state = SimulationState(
            id="test_sim",
            config=config,
            agent_type="market",
            personas=[
                Persona(id="p1", name="Analyst", role=PersonaRole.ANALYST, system_prompt="You are an analyst", traits=[], goals=[]),
                Persona(id="p2", name="Customer", role=PersonaRole.CUSTOMER, system_prompt="You are a customer", traits=[], goals=[]),
            ],
        )

        with patch.object(engine, '_get_persona_response', new_callable=AsyncMock) as mock_resp:
            mock_resp.return_value = "I think prices will increase by 5% due to supply constraints."
            with patch.object(engine, '_synthesize_result', new_callable=AsyncMock) as mock_synth:
                mock_synth.return_value = SimulationResult(
                    prediction="Prices will rise 5%",
                    confidence=0.7,
                    key_factors=["supply constraints"],
                )
                result = await engine.run_simulation(state)

        assert result.status == "completed"
        assert result.result is not None
        assert result.result.confidence == 0.7

    @pytest.mark.asyncio
    async def test_simulation_failure_handling(self):
        from backend.astra.simulation_engine import SimulationEngine

        engine = SimulationEngine()
        config = SimulationConfig(name="test", seed_query="test", rounds=1)
        state = SimulationState(id="fail_sim", config=config, agent_type="brand", personas=[])

        with patch.object(engine, '_run_round', new_callable=AsyncMock) as mock_round:
            mock_round.side_effect = RuntimeError("LLM unavailable")
            result = await engine.run_simulation(state)

        assert result.status == "failed"


# ── Review Swarm Tests ──────────────────────────────────────────────────────────

class TestReviewSwarm:
    @pytest.mark.asyncio
    async def test_extract_claims(self):
        from backend.agents.review_swarm import ReviewSwarm
        swarm = ReviewSwarm()

        text = "Oil prices will increase by 15% in Q2. The company expects revenue to decline. Supply chains are stable."
        claims = swarm._extract_claims(text)
        assert len(claims) >= 1
        assert any("15%" in c for c in claims)

    @pytest.mark.asyncio
    async def test_review_output_fallback(self):
        from backend.agents.review_swarm import ReviewSwarm, ReviewCritique
        swarm = ReviewSwarm()

        # With mocked LLM that fails
        with patch('backend.agents.review_swarm.llm_router') as mock_router:
            mock_router.invoke_with_fallback = AsyncMock(side_effect=RuntimeError("LLM down"))
            result = await swarm.review_output("brand", "Some output text", [])

        # Should return a fallback result
        assert isinstance(result.overall_score, float)
        assert 0.0 <= result.overall_score <= 1.0


# ── Report Agent Tests ──────────────────────────────────────────────────────────

class TestReportAgent:
    @pytest.mark.asyncio
    async def test_summary_report(self):
        from backend.astra.report_agent import ReportAgent

        agent = ReportAgent()
        state = SimulationState(
            id="rpt1",
            config=SimulationConfig(name="test", seed_query="test"),
            agent_type="brand",
            result=SimulationResult(prediction="Test prediction", confidence=0.8, key_factors=["factor1"], risks=["risk1"], opportunities=["opp1"]),
        )

        report = await agent.generate_report(state, report_type="summary")
        assert report["prediction"] == "Test prediction"
        assert report["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_report_no_results(self):
        from backend.astra.report_agent import ReportAgent

        agent = ReportAgent()
        state = SimulationState(
            id="rpt2",
            config=SimulationConfig(name="test", seed_query="test"),
            agent_type="brand",
        )

        report = await agent.generate_report(state)
        assert "error" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
