from typing import TypedDict, List, Optional, Annotated
from pydantic import BaseModel
import operator


class AgentOutput(BaseModel):
    agent: str
    confidence: float
    contribution: str
    key_points: List[str]
    model_used: str
    provider: str


class Evidence(BaseModel):
    type: str
    id: str
    tag: Optional[str] = None


class Action(BaseModel):
    type: str
    details: str
    cost_estimate: Optional[float] = None
    time_to_implement: Optional[str] = None


# ---------------------------------------------------------------------------
# Day 5: Debate Engine models
# ---------------------------------------------------------------------------
class DebateRound(BaseModel):
    """Structured output for a single debate round."""
    round_number: int
    phase: str  # "analysis" | "challenge" | "validation"
    agent_contributions: List[dict]  # [{agent, point, confidence, challenges}]
    key_disagreements: List[str]
    consensus_points: List[str]
    round_confidence: float  # 0-100 average across agents


class FallbackOption(BaseModel):
    """Tiered fallback option with cost/ROI analysis."""
    tier: int  # 1=immediate, 2=short-term, 3=strategic
    name: str
    description: str
    cost_estimate_usd: float
    time_to_implement_days: int
    risk_reduction_pct: float
    roi_pct: float
    confidence: float
    mcp_tool: Optional[str] = None  # MCP tool for one-click execution
    mcp_params: Optional[dict] = None


class Prediction(BaseModel):
    """Ensemble prediction with confidence intervals."""
    metric: str  # e.g. "price", "disruption_probability", "lead_time"
    horizon_days: int
    point_estimate: float
    ci_lower: float  # 95% CI lower
    ci_upper: float  # 95% CI upper
    confidence: float  # 0-1
    method: str  # "prophet" | "lstm_stub" | "monte_carlo" | "ensemble"
    data_points_used: int


class BrandSentiment(BaseModel):
    """Real-time brand sentiment analysis result."""
    overall_sentiment: str  # "positive" | "neutral" | "negative" | "crisis"
    sentiment_score: float  # -1.0 to 1.0
    trending_topics: List[str]
    crisis_keywords: List[str]
    recommended_actions: List[str]
    crisis_comm_draft: Optional[str] = None
    ad_pivot_recommendation: Optional[str] = None
    competitor_activity: Optional[str] = None


# ---------------------------------------------------------------------------
# Lite Mode models
# ---------------------------------------------------------------------------
class SupportEvidence(BaseModel):
    """Structured evidence payload from a lite-mode support subagent."""
    agent: str
    role: str = "support"
    summary: str  # Key findings in 3-5 bullets
    sources: List[str]  # e.g. ["[1]", "[2]", "[3]"]
    confidence: int  # 0-100
    flags: List[str]  # e.g. ["contradiction", "needs_verification"]
    links: List[str]  # Source URLs


class EvidenceBundle(BaseModel):
    """Merged evidence from all support subagents in lite mode."""
    support_evidence: List[SupportEvidence]
    citation_map: dict  # {"[1]": "https://...", ...}
    data_quality_summary: str
    conflicts: List[str]
    source_counts: dict  # {"risk": 5, "supply": 3, ...}


class SubagentEvidence(BaseModel):
    """Structured evidence from a single lite-mode subagent (data-channel + domain hybrid)."""
    subagent_key: str       # e.g. "risk_rag"
    parent_agent: str       # e.g. "risk"
    data_channel: str       # "rag" | "api" | "web" | "mcp" | "graph"
    domain_hint: str        # Domain focus description
    summary: str            # Key findings in 3-5 bullets
    sources: List[str]      # e.g. ["[1]", "[2]", "[3]"]
    confidence: int         # 0-100
    flags: List[str]        # e.g. ["contradiction", "needs_verification"]
    links: List[str]        # Source URLs


class LiteModeResult(BaseModel):
    """Final result from a lite-mode council run."""
    primary_agent: str
    evidence_bundle: EvidenceBundle
    final_answer: str
    confidence: float


def _list_reducer(current: list, update: list) -> list:
    return current + update if current else (update or [])


class CouncilState(TypedDict):
    query: str
    messages: Annotated[List[dict], operator.add]
    risk_score: Optional[float]
    recommendation: Optional[str]
    confidence: Optional[float]
    debate_history: Annotated[List[dict], operator.add]
    fallback_options: Annotated[List[Action], _list_reducer]
    agent_outputs: Annotated[List[AgentOutput], _list_reducer]
    evidence: Annotated[List[Evidence], _list_reducer]
    round_number: int
    llm_calls_log: Annotated[List[dict], operator.add]
    session_id: Optional[str]
    context: Optional[dict]
    # Day 5 additions
    debate_rounds: Annotated[List[dict], operator.add]  # DebateRound dicts
    predictions: Annotated[List[dict], operator.add]  # Prediction dicts
    tiered_fallbacks: Annotated[List[dict], operator.add]  # FallbackOption dicts
    brand_sentiment: Optional[dict]  # BrandSentiment dict
    human_approved: Optional[bool]
    # Lite Mode additions
    lite_mode: Optional[bool]
    primary_agent: Optional[str]
    support_evidence: Annotated[List[dict], _list_reducer]  # SupportEvidence dicts
    evidence_bundle: Optional[dict]  # EvidenceBundle dict
    subagent_evidence: Annotated[List[dict], _list_reducer]  # SubagentEvidence dicts
    # Astra ⭐ Integration
    astra_results: Optional[dict]  # Astra simulation results (brand + market)
