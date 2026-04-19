"""Tests for Lite Mode backend models, graph, and route logic."""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
from backend.state import SupportEvidence, EvidenceBundle, LiteModeResult, CouncilState, SubagentEvidence


class TestSupportEvidence:
    def test_create_minimal(self):
        e = SupportEvidence(
            agent="risk",
            summary="Key risk finding",
            sources=["[1]", "[2]"],
            confidence=75,
            flags=[],
            links=["https://example.com/1"],
        )
        assert e.agent == "risk"
        assert e.role == "support"
        assert e.confidence == 75
        assert len(e.sources) == 2

    def test_create_with_flags(self):
        e = SupportEvidence(
            agent="supply",
            summary="Contradiction found",
            sources=["[3]"],
            confidence=30,
            flags=["contradiction", "low_confidence"],
            links=[],
        )
        assert "contradiction" in e.flags
        assert "low_confidence" in e.flags

    def test_serialization(self):
        e = SupportEvidence(
            agent="market",
            summary="Market trend up",
            sources=["[1]"],
            confidence=80,
            flags=[],
            links=["https://example.com"],
        )
        d = e.model_dump()
        assert d["agent"] == "market"
        assert isinstance(d["sources"], list)
        json_str = json.dumps(d)
        assert "market" in json_str


class TestEvidenceBundle:
    def test_create_bundle(self):
        evidence = [
            SupportEvidence(agent="risk", summary="Risk up", sources=["[1]"], confidence=70, flags=[], links=[]),
            SupportEvidence(agent="supply", summary="Supply stable", sources=["[2]"], confidence=60, flags=[], links=[]),
        ]
        bundle = EvidenceBundle(
            support_evidence=evidence,
            citation_map={"[1]": "https://example.com/1"},
            data_quality_summary="Average support confidence: 65%. Data quality: Moderate.",
            conflicts=[],
            source_counts={"risk": 1, "supply": 1},
        )
        assert len(bundle.support_evidence) == 2
        assert bundle.citation_map["[1]"] == "https://example.com/1"
        assert bundle.data_quality_summary != ""

    def test_bundle_with_conflicts(self):
        bundle = EvidenceBundle(
            support_evidence=[],
            citation_map={},
            data_quality_summary="Weak",
            conflicts=["contradiction", "needs_verification"],
            source_counts={},
        )
        assert len(bundle.conflicts) == 2

    def test_serialization_round_trip(self):
        evidence = [
            SupportEvidence(agent="finance", summary="Revenue up", sources=["[5]"], confidence=90, flags=[], links=["https://fin.com"]),
        ]
        bundle = EvidenceBundle(
            support_evidence=evidence,
            citation_map={"[5]": "https://fin.com"},
            data_quality_summary="Strong",
            conflicts=[],
            source_counts={"finance": 1},
        )
        d = bundle.model_dump()
        restored = EvidenceBundle(**d)
        assert len(restored.support_evidence) == 1
        assert restored.support_evidence[0].agent == "finance"


class TestLiteModeResult:
    def test_create(self):
        bundle = EvidenceBundle(
            support_evidence=[],
            citation_map={},
            data_quality_summary="Moderate",
            conflicts=[],
            source_counts={},
        )
        result = LiteModeResult(
            primary_agent="risk",
            evidence_bundle=bundle,
            final_answer="Risk is moderate, supply is stable.",
            confidence=0.75,
        )
        assert result.primary_agent == "risk"
        assert result.confidence == 0.75


class TestCouncilStateLiteFields:
    def test_lite_mode_fields(self):
        state: CouncilState = {
            "query": "test query",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test-session",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
        }
        assert state["lite_mode"] is True
        assert state["primary_agent"] == "risk"


# ---------------------------------------------------------------------------
# Graph tests
# ---------------------------------------------------------------------------
from backend.graph import (
    build_lite_council_graph,
    evidence_merge_node,
    primary_synthesis_node,
    _lite_agent_fanout,
    AGENT_KEYS,
)


class TestLiteGraph:
    def test_agent_keys_defined(self):
        assert AGENT_KEYS == ["risk", "supply", "logistics", "market", "finance", "brand"]

    def test_build_lite_graph(self):
        graph = build_lite_council_graph()
        assert graph is not None
        # Compile to verify structure
        compiled = graph.compile()
        assert compiled is not None

    def test_lite_agent_fanout_default(self):
        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [],
        }
        result = _lite_agent_fanout(state)
        # All 6 agents should be in the fanout
        assert set(result.keys()) == set(AGENT_KEYS)

    def test_lite_agent_fanout_with_active_agents(self):
        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {"active_agents": ["risk", "supply", "market"]},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [],
        }
        result = _lite_agent_fanout(state)
        assert set(result.keys()) == {"risk", "supply", "market"}


class TestEvidenceMergeNode:
    @pytest.mark.asyncio
    async def test_merge_empty_outputs(self):
        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [],
        }
        result = await evidence_merge_node(state)
        assert "evidence_bundle" in result
        assert "support_evidence" in result
        assert result["evidence_bundle"] is not None

    @pytest.mark.asyncio
    async def test_merge_skips_primary_agent(self):
        mock_output = MagicMock()
        mock_output.agent = "risk"
        mock_output.contribution = "Primary analysis"
        mock_output.confidence = 85

        mock_support = MagicMock()
        mock_support.agent = "supply"
        mock_support.contribution = "Supply is stable"
        mock_support.confidence = 70

        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [mock_output, mock_support],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [],
        }
        result = await evidence_merge_node(state)
        bundle = result["evidence_bundle"]
        # Primary agent (risk) should be excluded from support evidence
        agent_names = [e["agent"] for e in bundle["support_evidence"]]
        assert "risk" not in agent_names
        assert "supply" in agent_names


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------
from backend.routes.council_v2 import CouncilV2Request


class TestCouncilV2Request:
    def test_lite_mode_request(self):
        req = CouncilV2Request(
            query="Test query",
            lite_mode=True,
            primary_agent="risk",
            support_agents=["supply", "logistics", "market", "finance", "brand"],
            support_agent_policy={"rag": True, "api": True, "mcp": True, "web": False, "graph": True},
        )
        assert req.lite_mode is True
        assert req.primary_agent == "risk"
        assert len(req.support_agents) == 5
        assert req.support_agent_policy["web"] is False

    def test_default_policy(self):
        req = CouncilV2Request(query="Test")
        assert req.support_agent_policy is None
        assert req.lite_mode is None

    def test_full_council_request(self):
        req = CouncilV2Request(
            query="Full council query",
            lite_mode=False,
        )
        assert req.lite_mode is False


# ---------------------------------------------------------------------------
# SubagentEvidence model tests
# ---------------------------------------------------------------------------
class TestSubagentEvidence:
    def test_create_minimal(self):
        se = SubagentEvidence(
            subagent_key="risk_rag",
            parent_agent="risk",
            data_channel="rag",
            domain_hint="geopolitical risk documents",
            summary="Found 3 key risk indicators",
            sources=["[1]", "[2]"],
            confidence=78,
            flags=[],
            links=["https://example.com/risk1"],
        )
        assert se.subagent_key == "risk_rag"
        assert se.parent_agent == "risk"
        assert se.data_channel == "rag"
        assert se.confidence == 78

    def test_serialization_round_trip(self):
        se = SubagentEvidence(
            subagent_key="supply_api",
            parent_agent="supply",
            data_channel="api",
            domain_hint="supplier APIs",
            summary="API data collected",
            sources=["[1]"],
            confidence=65,
            flags=["needs_verification"],
            links=[],
        )
        data = se.model_dump()
        restored = SubagentEvidence(**data)
        assert restored.subagent_key == "supply_api"
        assert restored.flags == ["needs_verification"]


# ---------------------------------------------------------------------------
# Subagent Registry tests
# ---------------------------------------------------------------------------
from backend.agents.subagent_registry import SUBAGENT_REGISTRY, SUBAGENT_CHANNELS, build_subagent_registry


class TestSubagentRegistry:
    def test_all_agents_have_5_subagents(self):
        for agent_key in ["risk", "supply", "logistics", "market", "finance", "brand"]:
            defs = SUBAGENT_REGISTRY[agent_key]
            assert len(defs) == 5, f"{agent_key} has {len(defs)} subagents, expected 5"

    def test_subagent_keys_are_unique(self):
        all_keys = []
        for defs in SUBAGENT_REGISTRY.values():
            all_keys.extend(d["key"] for d in defs)
        assert len(all_keys) == len(set(all_keys)), "Duplicate subagent keys found"

    def test_all_channels_covered(self):
        for agent_key, defs in SUBAGENT_REGISTRY.items():
            channels = {d["data_channel"] for d in defs}
            assert channels == set(SUBAGENT_CHANNELS), f"{agent_key} missing channels: {set(SUBAGENT_CHANNELS) - channels}"

    def test_domain_hints_populated(self):
        for agent_key, defs in SUBAGENT_REGISTRY.items():
            for d in defs:
                assert d["domain_hint"], f"{d['key']} has empty domain_hint"

    def test_system_prompt_templates_have_placeholders(self):
        for agent_key, defs in SUBAGENT_REGISTRY.items():
            for d in defs:
                assert "{parent_agent}" in d["system_prompt_template"], f"{d['key']} missing {{parent_agent}}"
                assert "{domain_hint}" in d["system_prompt_template"], f"{d['key']} missing {{domain_hint}}"

    def test_build_subagent_registry_deterministic(self):
        r1 = build_subagent_registry()
        r2 = build_subagent_registry()
        for key in r1:
            assert [d["key"] for d in r1[key]] == [d["key"] for d in r2[key]]


# ---------------------------------------------------------------------------
# Evidence Merge with SubagentEvidence tests
# ---------------------------------------------------------------------------
class TestEvidenceMergeWithSubagents:
    @pytest.mark.asyncio
    async def test_merge_with_subagent_evidence(self):
        se1 = SubagentEvidence(
            subagent_key="risk_rag",
            parent_agent="risk",
            data_channel="rag",
            domain_hint="risk docs",
            summary="RAG finding 1",
            sources=["[1]"],
            confidence=80,
            flags=[],
            links=[],
        )
        se2 = SubagentEvidence(
            subagent_key="risk_api",
            parent_agent="risk",
            data_channel="api",
            domain_hint="risk APIs",
            summary="API finding 2",
            sources=["[2]"],
            confidence=70,
            flags=["needs_verification"],
            links=["https://api.example.com"],
        )
        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "risk",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [se1.model_dump(), se2.model_dump()],
        }
        result = await evidence_merge_node(state)
        bundle = result["evidence_bundle"]
        assert bundle is not None
        # Should have 2 support evidence items from subagents
        assert len(bundle["support_evidence"]) == 2
        # Source counts should be by channel
        assert "rag" in bundle["source_counts"]
        assert "api" in bundle["source_counts"]
        # Conflicts should include subagent flags
        assert "needs_verification" in bundle["conflicts"]

    @pytest.mark.asyncio
    async def test_merge_subagent_evidence_preserved(self):
        se = SubagentEvidence(
            subagent_key="market_web",
            parent_agent="market",
            data_channel="web",
            domain_hint="market web",
            summary="Web finding",
            sources=["[1]"],
            confidence=60,
            flags=[],
            links=[],
        )
        state: CouncilState = {
            "query": "test",
            "messages": [],
            "risk_score": None,
            "recommendation": None,
            "confidence": None,
            "debate_history": [],
            "fallback_options": [],
            "agent_outputs": [],
            "evidence": [],
            "round_number": 0,
            "llm_calls_log": [],
            "session_id": "test",
            "context": {},
            "debate_rounds": [],
            "predictions": [],
            "tiered_fallbacks": [],
            "brand_sentiment": None,
            "human_approved": None,
            "lite_mode": True,
            "primary_agent": "market",
            "support_evidence": [],
            "evidence_bundle": None,
            "subagent_evidence": [se.model_dump()],
        }
        result = await evidence_merge_node(state)
        # Subagent evidence should be passed through
        assert "subagent_evidence" in result
        assert len(result["subagent_evidence"]) == 1
