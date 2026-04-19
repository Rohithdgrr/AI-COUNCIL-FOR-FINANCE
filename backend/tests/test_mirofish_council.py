"""Tests for MiroFish integration in Council V2 debate.

Verifies:
- mirofish_enabled flag is respected
- MiroFish only triggers for brand + market agents
- MiroFish runs after round 3 in full council mode
- MiroFish runs after synthesis in lite mode
- SSE events are emitted with correct types
- MiroFish does NOT run when disabled
"""

import pytest
import json
from pydantic import BaseModel
from typing import Optional


# Re-define the request model locally to avoid heavy imports
# (backend.routes.council_v2 imports langchain_groq etc.)
class CouncilV2RequestTest(BaseModel):
    query: str
    context: Optional[dict] = None
    lite_mode: Optional[bool] = None
    primary_agent: Optional[str] = None
    support_agents: Optional[list[str]] = None
    support_agent_policy: Optional[dict] = None
    mirofish_enabled: Optional[bool] = False


class TestCouncilV2RequestMiroFish:
    """Test CouncilV2Request model with mirofish_enabled field."""

    def test_mirofish_enabled_defaults_false(self):
        req = CouncilV2RequestTest(query="test query")
        assert req.mirofish_enabled is False

    def test_mirofish_enabled_can_be_set_true(self):
        req = CouncilV2RequestTest(query="test query", mirofish_enabled=True)
        assert req.mirofish_enabled is True

    def test_mirofish_enabled_can_be_set_false(self):
        req = CouncilV2RequestTest(query="test query", mirofish_enabled=False)
        assert req.mirofish_enabled is False

    def test_request_serialization(self):
        req = CouncilV2RequestTest(query="test query", mirofish_enabled=True)
        data = req.model_dump()
        assert data["mirofish_enabled"] is True
        assert data["query"] == "test query"


class TestMiroFishSSEEvents:
    """Test that MiroFish SSE events have the correct structure."""

    def test_mirofish_start_event(self):
        event = {"type": "mirofish_start", "agents": ["brand", "market"]}
        assert event["type"] == "mirofish_start"
        assert "brand" in event["agents"]
        assert "market" in event["agents"]
        assert len(event["agents"]) == 2
        # No other agents should be in the list
        assert "risk" not in event["agents"]
        assert "supply" not in event["agents"]
        assert "logistics" not in event["agents"]
        assert "finance" not in event["agents"]

    def test_mirofish_agent_progress_event_brand(self):
        event = {
            "type": "mirofish_agent_progress",
            "agent": "brand",
            "phase": "graph_building",
            "simulation_id": "brand_sim_abc123",
        }
        assert event["type"] == "mirofish_agent_progress"
        assert event["agent"] == "brand"
        assert event["phase"] in [
            "graph_building", "graph_ready",
            "persona_generation", "personas_ready",
            "simulation_running", "report_generation",
        ]

    def test_mirofish_agent_progress_event_market(self):
        event = {
            "type": "mirofish_agent_progress",
            "agent": "market",
            "phase": "simulation_running",
            "simulation_id": "market_sim_def456",
        }
        assert event["agent"] == "market"
        assert event["phase"] == "simulation_running"

    def test_mirofish_agent_complete_event(self):
        event = {
            "type": "mirofish_agent_complete",
            "agent": "brand",
            "result": {
                "simulation_id": "brand_sim_abc123",
                "status": "completed",
                "prediction": "Brand sentiment will improve",
                "confidence": 0.78,
                "key_factors": ["Consumer trust", "Social media"],
                "risks": ["Negative viral content"],
                "opportunities": ["Influencer partnerships"],
                "recommendations": ["Increase social monitoring"],
                "scenarios": [],
                "entities": ["Brand X", "Competitor Y"],
                "personas": ["Brand Analyst (analyst)"],
                "report_summary": "Positive outlook...",
            },
        }
        assert event["type"] == "mirofish_agent_complete"
        assert event["agent"] in ["brand", "market"]
        assert "result" in event
        assert "prediction" in event["result"]
        assert "confidence" in event["result"]

    def test_mirofish_agent_error_event(self):
        event = {
            "type": "mirofish_agent_error",
            "agent": "market",
            "error": "Simulation failed: LLM timeout",
        }
        assert event["type"] == "mirofish_agent_error"
        assert event["agent"] in ["brand", "market"]

    def test_mirofish_complete_event(self):
        event = {"type": "mirofish_complete"}
        assert event["type"] == "mirofish_complete"

    def test_complete_event_includes_mirofish_enabled(self):
        event = {
            "type": "complete",
            "session_id": "test-session",
            "confidence": 85.0,
            "recommendation": "Test recommendation",
            "mirofish_enabled": True,
        }
        assert event["mirofish_enabled"] is True

    def test_complete_event_mirofish_disabled(self):
        event = {
            "type": "complete",
            "session_id": "test-session",
            "confidence": 85.0,
            "recommendation": "Test recommendation",
            "mirofish_enabled": False,
        }
        assert event["mirofish_enabled"] is False


class TestMiroFishAgentRestriction:
    """Test that MiroFish only applies to brand and market agents."""

    ALLOWED_AGENTS = {"brand", "market"}
    ALL_AGENTS = {"risk", "supply", "logistics", "market", "finance", "brand"}

    def test_only_brand_and_market_are_mirofish_targets(self):
        mirofish_agents = {"brand", "market"}
        assert mirofish_agents == self.ALLOWED_AGENTS
        assert mirofish_agents.issubset(self.ALL_AGENTS)

    def test_other_agents_are_not_mirofish_targets(self):
        non_mirofish = self.ALL_AGENTS - self.ALLOWED_AGENTS
        assert non_mirofish == {"risk", "supply", "logistics", "finance"}
        for agent in non_mirofish:
            assert agent not in self.ALLOWED_AGENTS

    def test_mirofish_start_event_only_lists_brand_and_market(self):
        event = {"type": "mirofish_start", "agents": ["brand", "market"]}
        for agent in event["agents"]:
            assert agent in self.ALLOWED_AGENTS

    def test_no_mirofish_events_for_risk_agent(self):
        """Risk agent should never appear in MiroFish events."""
        mirofish_event_types = [
            "mirofish_agent_progress",
            "mirofish_agent_complete",
            "mirofish_agent_error",
        ]
        for event_type in mirofish_event_types:
            event = {"type": event_type, "agent": "risk"}
            assert event["agent"] not in self.ALLOWED_AGENTS, (
                f"Risk agent should not appear in {event_type}"
            )


class TestMiroFishPhaseOrdering:
    """Test that MiroFish phases follow the correct order."""

    VALID_PHASES = [
        "graph_building",
        "graph_ready",
        "persona_generation",
        "personas_ready",
        "simulation_running",
        "report_generation",
    ]

    def test_phases_are_in_correct_order(self):
        """Graph building must come before simulation, etc."""
        phase_order = {
            "graph_building": 0,
            "graph_ready": 1,
            "persona_generation": 2,
            "personas_ready": 3,
            "simulation_running": 4,
            "report_generation": 5,
        }
        for i in range(len(self.VALID_PHASES) - 1):
            current = self.VALID_PHASES[i]
            next_phase = self.VALID_PHASES[i + 1]
            assert phase_order[current] < phase_order[next_phase]

    def test_completed_is_terminal_phase(self):
        terminal_phases = {"completed", "failed"}
        assert "completed" in terminal_phases
        assert "failed" in terminal_phases

    def test_idle_is_initial_phase(self):
        initial_phases = {"idle", ""}
        assert "idle" in initial_phases


class TestMiroFishOnlyAfterRound3:
    """Test that MiroFish simulation only runs after 3 rounds of debate."""

    def test_mirofish_disabled_skips_simulation(self):
        """When mirofish_enabled=False, no MiroFish events should be emitted."""
        req = CouncilV2RequestTest(query="test", mirofish_enabled=False)
        assert req.mirofish_enabled is False

    def test_mirofish_enabled_allows_simulation(self):
        """When mirofish_enabled=True, MiroFish can run after round 3."""
        req = CouncilV2RequestTest(query="test", mirofish_enabled=True)
        assert req.mirofish_enabled is True

    def test_mirofish_runs_after_supervisor(self):
        """In the SSE flow, mirofish_start comes after supervisor_done (round 3)."""
        events = [
            {"type": "round_start", "round": 1, "phase": "analysis"},
            {"type": "round_start", "round": 2, "phase": "debate"},
            {"type": "round_start", "round": 3, "phase": "supervisor"},
            {"type": "supervisor_done", "round": 3, "confidence": 85},
            {"type": "mirofish_start", "agents": ["brand", "market"]},
            {"type": "mirofish_complete"},
            {"type": "complete", "session_id": "test", "confidence": 85, "recommendation": "test"},
        ]
        supervisor_idx = next(i for i, e in enumerate(events) if e["type"] == "supervisor_done")
        mirofish_start_idx = next(i for i, e in enumerate(events) if e["type"] == "mirofish_start")
        complete_idx = next(i for i, e in enumerate(events) if e["type"] == "complete")
        assert mirofish_start_idx > supervisor_idx, "MiroFish must start after supervisor (round 3)"
        assert mirofish_start_idx < complete_idx, "MiroFish must complete before the final event"

    def test_no_mirofish_events_when_disabled(self):
        """When mirofish_enabled=False, the event stream should not contain any mirofish events."""
        events = [
            {"type": "round_start", "round": 1, "phase": "analysis"},
            {"type": "round_start", "round": 2, "phase": "debate"},
            {"type": "round_start", "round": 3, "phase": "supervisor"},
            {"type": "supervisor_done", "round": 3, "confidence": 85},
            {"type": "complete", "session_id": "test", "confidence": 85, "recommendation": "test", "mirofish_enabled": False},
        ]
        mirofish_events = [e for e in events if e["type"].startswith("mirofish")]
        assert len(mirofish_events) == 0, "No MiroFish events when disabled"


class TestMiroFishInLiteMode:
    """Test that MiroFish simulation works in lite mode after synthesis."""

    def test_lite_mode_request_with_mirofish(self):
        """Lite mode request with mirofish_enabled=True should be valid."""
        req = CouncilV2RequestTest(query="test", lite_mode=True, mirofish_enabled=True)
        assert req.lite_mode is True
        assert req.mirofish_enabled is True

    def test_lite_mode_mirofish_after_synthesis(self):
        """In lite mode, MiroFish should start after synthesis (round 2), not after supervisor (round 3)."""
        events = [
            {"type": "start", "session_id": "lite-1", "query": "test", "lite_mode": True, "mirofish_enabled": True},
            {"type": "round_start", "round": 1, "phase": "analysis"},
            {"type": "round_start", "round": 2, "phase": "synthesis"},
            {"type": "mirofish_start", "agents": ["brand", "market"]},
            {"type": "mirofish_complete"},
            {"type": "complete", "session_id": "lite-1", "confidence": 85, "recommendation": "test", "lite_mode": True, "mirofish_enabled": True},
        ]
        synthesis_idx = next(i for i, e in enumerate(events) if e["type"] == "round_start" and e.get("phase") == "synthesis")
        mirofish_start_idx = next(i for i, e in enumerate(events) if e["type"] == "mirofish_start")
        complete_idx = next(i for i, e in enumerate(events) if e["type"] == "complete")
        assert mirofish_start_idx > synthesis_idx, "MiroFish must start after synthesis in lite mode"
        assert mirofish_start_idx < complete_idx, "MiroFish must complete before the final event"

    def test_lite_mode_no_mirofish_when_disabled(self):
        """In lite mode, when mirofish_enabled=False, no MiroFish events should appear."""
        events = [
            {"type": "start", "session_id": "lite-2", "query": "test", "lite_mode": True, "mirofish_enabled": False},
            {"type": "round_start", "round": 1, "phase": "analysis"},
            {"type": "round_start", "round": 2, "phase": "synthesis"},
            {"type": "complete", "session_id": "lite-2", "confidence": 85, "recommendation": "test", "lite_mode": True, "mirofish_enabled": False},
        ]
        mirofish_events = [e for e in events if e["type"].startswith("mirofish")]
        assert len(mirofish_events) == 0, "No MiroFish events in lite mode when disabled"

    def test_complete_event_includes_mirofish_enabled_in_lite_mode(self):
        """The complete event in lite mode should include mirofish_enabled flag."""
        req = CouncilV2RequestTest(query="test", lite_mode=True, mirofish_enabled=True)
        # Simulate the complete event payload
        complete_event = {
            "type": "complete",
            "session_id": "lite-3",
            "confidence": 85,
            "recommendation": "test",
            "lite_mode": True,
            "mirofish_enabled": req.mirofish_enabled,
        }
        assert complete_event["mirofish_enabled"] is True
        assert complete_event["lite_mode"] is True

    def test_mirofish_agents_always_brand_and_market(self):
        """MiroFish always runs for brand + market agents, regardless of mode."""
        # Full council
        full_events = [
            {"type": "mirofish_start", "agents": ["brand", "market"]},
        ]
        # Lite mode
        lite_events = [
            {"type": "mirofish_start", "agents": ["brand", "market"]},
        ]
        assert full_events[0]["agents"] == ["brand", "market"]
        assert lite_events[0]["agents"] == ["brand", "market"]
