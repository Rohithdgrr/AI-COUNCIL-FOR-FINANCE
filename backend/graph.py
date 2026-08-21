from langgraph.graph import StateGraph, END
from langgraph.constants import Send
from backend.state import CouncilState
from backend.agents.moderator import moderator_parse, moderator_synthesize
from backend.agents.risk_agent import risk_agent
from backend.agents.supply_agent import supply_agent
from backend.agents.logistics_agent import logistics_agent
from backend.agents.market_agent import market_agent
from backend.agents.finance_agent import finance_agent
from backend.agents.brand_agent import brand_agent
from backend.graph_utils import node_error_handler
from backend.graph_astra_integration import astra_parallel_node
import logging
import json
import time

from backend.config import settings

logger = logging.getLogger(__name__)

AGENT_KEYS = ["risk", "supply", "logistics", "market", "finance", "brand"]


# ---------------------------------------------------------------------------
# Dynamic Agent Routing node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"context": {}})
async def dynamic_routing_node(state: CouncilState) -> dict:
    """Determine which agents to activate based on query content.

    Uses keyword scoring + optional LLM classification to select
    the most relevant agents, reducing unnecessary LLM calls.

    Stores selected agents in context.active_agents for the graph
    to use in conditional edges.
    """
    query = state.get("query", "")
    ctx = state.get("context") or {}

    # Check if caller explicitly specified agents
    explicit_agents = ctx.get("active_agents")
    if explicit_agents and isinstance(explicit_agents, list):
        logger.info(f"Using explicitly specified agents: {explicit_agents}")
        return {"context": {**ctx, "active_agents": explicit_agents}}

    # Dynamic routing
    from backend.agents.dynamic_routing import route_query
    use_llm = ctx.get("debate_config", {}).get("use_llm_routing", True)
    selected = await route_query(query, use_llm=use_llm)

    return {"context": {**ctx, "active_agents": selected}}


# ---------------------------------------------------------------------------
# Day 3: RAG Pre-fetch node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"context": {"rag_contexts": {}}})
async def rag_prefetch(state: CouncilState) -> dict:
    """RAG pre-fetch node: fetch context for all agents before fan-out."""
    query = state.get("query", "")
    if not query:
        return {"context": {**(state.get("context") or {}), "rag_contexts": {}}}

    from backend.rag.agent_rag_integration import prefetch_rag_for_all_agents
    rag_contexts = await prefetch_rag_for_all_agents(query)
    logger.info(f"RAG prefetch complete for {len(rag_contexts)} agents")
    return {"context": {**(state.get("context") or {}), "rag_contexts": rag_contexts}}


# ---------------------------------------------------------------------------
# Day 4: MCP Escalation node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"context": {"rag_meta": {}, "mcp_contexts": {}}})
async def mcp_escalation(state: CouncilState) -> dict:
    """MCP escalation node: auto-call MCP tools for agents with low RAG confidence."""
    query = state.get("query", "")
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {} if context else {}

    rag_meta = {}
    for agent_name, rag_ctx in rag_contexts.items():
        confidence = 0.0
        if "confidence:" in rag_ctx:
            try:
                import re
                match = re.search(r"confidence:\s*(\d+)%", rag_ctx)
                if match:
                    confidence = int(match.group(1)) / 100.0
            except Exception:
                pass
        rag_meta[agent_name] = confidence

    if not query:
        return {"context": {**context, "rag_meta": rag_meta, "mcp_contexts": {}}}

    from backend.mcp.agent_mcp_integration import prefetch_mcp_for_all_agents
    mcp_contexts = await prefetch_mcp_for_all_agents(query, rag_confidences=rag_meta)
    escalated = [n for n, c in mcp_contexts.items() if c]
    if escalated:
        logger.info(f"MCP escalation: auto-called tools for agents {escalated}")
    return {"context": {**context, "rag_meta": rag_meta, "mcp_contexts": mcp_contexts}}


# ---------------------------------------------------------------------------
# Day 5: Predictions node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"predictions": []})
async def predictions_node(state: CouncilState) -> dict:
    """Generate ensemble predictions (price, disruption, lead time) for the debate."""
    query = state.get("query", "")
    if not query:
        return {"predictions": []}

    from backend.predictions_engine import generate_predictions_for_debate
    preds = await generate_predictions_for_debate(query, state)
    logger.info(f"Generated {len(preds)} predictions")
    return {"predictions": preds}


# ---------------------------------------------------------------------------
# Day 5: Debate Engine node
# ---------------------------------------------------------------------------
@node_error_handler(
    fallback={
        "debate_rounds": [],
        "confidence": 0.0,
        "risk_score": 50.0,
        "recommendation": "Debate engine failed",
        "fallback_options": [],
    },
    log_level="error",
)
async def debate_node(state: CouncilState) -> dict:
    """Run the 3-round structured debate engine.

    After all agents have contributed, the DebateEngine orchestrates:
      Round 1: Parallel Analysis summary
      Self-critique: Agents review their own analysis (optional)
      Round 2: Challenge & Counter phase (skipped in lite mode)
      Round 3: Validation & Synthesis

    Supports per-request overrides for lite_mode and enable_self_critique
    via state.context.debate_config.

    Produces: debate_rounds, confidence, risk_score, recommendation, fallback_options
    """
    from backend.debate_engine import DebateEngine
    from backend.config import settings as _s

    # Per-request overrides from context
    ctx = state.get("context") or {}
    debate_config = ctx.get("debate_config") or {}
    lite = debate_config.get("lite", _s.council_lite_mode)
    self_critique = debate_config.get("enable_self_critique", _s.enable_self_critique)

    engine = DebateEngine(
        max_rounds=_s.max_debate_rounds,
        consensus_threshold=_s.confidence_gap_threshold,
        lite_mode=lite,
        enable_self_critique=self_critique,
    )
    result = await engine.run_debate(state)
    logger.info(
        f"Debate complete: {len(result.get('debate_rounds', []))} rounds, "
        f"confidence={result.get('confidence', 0):.2f}, "
        f"risk={result.get('risk_score', 0):.1f}, "
        f"lite={lite}, self_critique={self_critique}"
    )
    return result


# ---------------------------------------------------------------------------
# Day 5: Fallback Engine node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"tiered_fallbacks": []})
async def fallback_node(state: CouncilState) -> dict:
    """Generate tiered fallback options based on debate and prediction results."""
    from backend.fallback_engine import fallback_engine
    result = await fallback_engine.generate_fallbacks(state)
    n = len(result.get("tiered_fallbacks", []))
    logger.info(f"Generated {n} tiered fallback options")
    return result


# ---------------------------------------------------------------------------
# Day 5: Brand Enhancement node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"brand_sentiment": None})
async def brand_enhancement_node(state: CouncilState) -> dict:
    """Run brand sentiment analysis, crisis comms, ad pivot, and competitor analysis."""
    from backend.brand_agent_enhancement import brand_enhancer
    result = await brand_enhancer.run_full_enhancement(state)
    sentiment = result.get("brand_sentiment", {})
    logger.info(f"Brand enhancement: sentiment={sentiment.get('overall_sentiment', 'unknown')}")
    return result


# ---------------------------------------------------------------------------
# Day 5: Conditional edge — should we run brand enhancement?
# ---------------------------------------------------------------------------
def needs_brand_enhancement(state: CouncilState) -> str:
    """Route to brand enhancement if brand agent detected negative sentiment."""
    agent_outputs = state.get("agent_outputs", [])
    for o in agent_outputs:
        if o.agent == "brand" and o.confidence < 50:
            return "brand_enhancement"
    # Check if query mentions brand/reputation/PR keywords
    query = (state.get("query") or "").lower()
    brand_keywords = ["brand", "reputation", "pr", "crisis", "sentiment", "social media", "consumer"]
    if any(kw in query for kw in brand_keywords):
        return "brand_enhancement"
    return "skip_brand"


# ---------------------------------------------------------------------------
# Build the full council graph
# ---------------------------------------------------------------------------

def _agent_should_run(agent_name: str, state: CouncilState) -> bool:
    """Check if an agent should run based on dynamic routing results."""
    ctx = state.get("context") or {}
    active_agents = ctx.get("active_agents")
    if not active_agents:
        return True
    return agent_name in active_agents


def _agent_fanout(state: CouncilState):
    """Single routing function for all agents — eliminates race condition from multiple conditional edges."""
    AGENT_NAMES = ["risk", "supply", "logistics", "market", "finance", "brand"]
    targets = []
    for name in AGENT_NAMES:
        if _agent_should_run(name, state):
            targets.append(Send(name, state))
    if not targets:
        targets.append(Send("predictions_step", state))
    return targets


def build_council_graph() -> StateGraph:
    graph = StateGraph(CouncilState)

    # Add all nodes
    graph.add_node("moderator", moderator_parse)
    graph.add_node("dynamic_routing", dynamic_routing_node)
    graph.add_node("rag_prefetch", rag_prefetch)
    graph.add_node("mcp_escalation", mcp_escalation)
    graph.add_node("astra_parallel", astra_parallel_node)  # ⭐ Astra integration
    graph.add_node("risk", risk_agent)
    graph.add_node("supply", supply_agent)
    graph.add_node("logistics", logistics_agent)
    graph.add_node("market", market_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("brand", brand_agent)
    graph.add_node("predictions_step", predictions_node)
    graph.add_node("debate", debate_node)
    graph.add_node("fallback", fallback_node)
    graph.add_node("brand_enhancement", brand_enhancement_node)
    graph.add_node("synthesize", moderator_synthesize)

    graph.set_entry_point("moderator")

    # Phase 1: Moderator → Dynamic Routing → RAG → MCP → Astra (parallel) → Agent fan-out
    graph.add_edge("moderator", "dynamic_routing")
    graph.add_edge("dynamic_routing", "rag_prefetch")
    graph.add_edge("rag_prefetch", "mcp_escalation")
    graph.add_edge("mcp_escalation", "astra_parallel")  # ⭐ Astra runs in parallel

    # Single conditional edge for all agents — returns dict of all agents that should run
    graph.add_conditional_edges("astra_parallel", _agent_fanout, [
        "risk", "supply", "logistics", "market", "finance", "brand", "predictions_step"
    ])

    # Phase 2: All agents converge to predictions node
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge(agent, "predictions_step")

    graph.add_edge("predictions_step", "debate")
    graph.add_edge("debate", "fallback")

    # Phase 3: Conditional brand enhancement
    graph.add_conditional_edges("fallback", needs_brand_enhancement, {
        "brand_enhancement": "brand_enhancement",
        "skip_brand": "synthesize",
    })
    graph.add_edge("brand_enhancement", "synthesize")

    # Final synthesis
    graph.add_edge("synthesize", END)

    return graph


# ---------------------------------------------------------------------------
# Lite Mode: Evidence Merge node
# ---------------------------------------------------------------------------
@node_error_handler(fallback={"evidence_bundle": None, "support_evidence": [], "subagent_evidence": []})
async def evidence_merge_node(state: CouncilState) -> dict:
    """Merge all support agent outputs into a structured EvidenceBundle.

    Handles both legacy support agent outputs and new SubagentEvidence
    from the hybrid subagent runner.
    """
    from backend.state import SupportEvidence, EvidenceBundle, SubagentEvidence

    agent_outputs = state.get("agent_outputs", [])
    context = state.get("context") or {}
    primary_agent = state.get("primary_agent") or context.get("primary_agent", "risk")

    # Check if we have subagent evidence (new hybrid approach)
    existing_subagent_evidence = state.get("subagent_evidence", [])

    all_support_evidence: list[SupportEvidence] = []
    citation_map: dict = {}
    source_counts: dict = {}
    conflicts: list[str] = []

    # If subagent evidence exists, convert to SupportEvidence
    if existing_subagent_evidence:
        for se_dict in existing_subagent_evidence:
            se = SubagentEvidence(**se_dict) if isinstance(se_dict, dict) else se_dict
            support_ev = SupportEvidence(
                agent=se.parent_agent,
                role=f"subagent:{se.data_channel}",
                summary=f"[{se.data_channel.upper()}] {se.summary[:400]}",
                sources=se.sources,
                confidence=se.confidence,
                flags=se.flags,
                links=se.links,
            )
            all_support_evidence.append(support_ev)
            source_counts[se.data_channel] = source_counts.get(se.data_channel, 0) + len(se.sources)
            conflicts.extend(se.flags)
    else:
        # Legacy path: merge from agent_outputs
        for ao in agent_outputs:
            if ao.agent == primary_agent:
                continue

            output_text = ao.contribution if hasattr(ao, "contribution") else str(ao)
            confidence = ao.confidence if hasattr(ao, "confidence") else 0

            rag_contexts = context.get("rag_contexts") or {}
            mcp_contexts = context.get("mcp_contexts") or {}
            agent_rag = rag_contexts.get(ao.agent, "")
            agent_mcp = mcp_contexts.get(ao.agent, "")

            source_refs: list[str] = []
            links: list[str] = []
            if agent_rag:
                import re as _re
                for m in _re.finditer(r"\[(\d+)\]", agent_rag):
                    source_refs.append(f"[{m.group(1)}]")
            if agent_mcp:
                import re as _re
                for m in _re.finditer(r"https?://\S+", agent_mcp):
                    links.append(m.group(0).rstrip(")"))

            flags: list[str] = []
            if "contradiction" in output_text.lower() or "conflict" in output_text.lower():
                flags.append("contradiction")
            if "verify" in output_text.lower() or "unconfirmed" in output_text.lower():
                flags.append("needs_verification")
            if confidence < 40:
                flags.append("low_confidence")
            conflicts.extend(flags)

            evidence = SupportEvidence(
                agent=ao.agent,
                role="support",
                summary=output_text[:500] if output_text else "No evidence collected",
                sources=source_refs[:10],
                confidence=int(confidence),
                flags=flags,
                links=links[:8],
            )
            all_support_evidence.append(evidence)
            source_counts[ao.agent] = len(source_refs)

    avg_conf = sum(e.confidence for e in all_support_evidence) / max(len(all_support_evidence), 1)
    quality = "Strong" if avg_conf >= 70 else "Moderate" if avg_conf >= 40 else "Weak"

    evidence_bundle = EvidenceBundle(
        support_evidence=all_support_evidence,
        citation_map=citation_map,
        data_quality_summary=f"Average subagent confidence: {avg_conf:.0f}%. Data quality: {quality}. {len(existing_subagent_evidence)} subagents ran." if existing_subagent_evidence else f"Average support confidence: {avg_conf:.0f}%. Data quality: {quality}.",
        conflicts=list(set(conflicts)),
        source_counts=source_counts,
    )

    logger.info(
        f"Evidence merge complete: {len(all_support_evidence)} evidence items, "
        f"avg_conf={avg_conf:.0f}, quality={quality}"
    )
    return {
        "evidence_bundle": evidence_bundle.model_dump(),
        "support_evidence": [e.model_dump() for e in all_support_evidence],
        "subagent_evidence": existing_subagent_evidence,
    }


# ---------------------------------------------------------------------------
# Lite Mode: Primary Synthesis node
# ---------------------------------------------------------------------------
@node_error_handler(
    fallback={
        "recommendation": "Primary synthesis failed",
        "confidence": 0.0,
        "risk_score": 50.0,
    },
    log_level="error",
)
async def primary_synthesis_node(state: CouncilState) -> dict:
    """Primary agent synthesizes the final answer from merged evidence.

    Uses the primary agent's prompt + the evidence bundle to produce
    a single final answer with citations and confidence.
    """
    from backend.llm.router import llm_router
    from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
    from backend.agents.supply_agent import SYSTEM_PROMPT as SUPPLY_PROMPT
    from backend.agents.logistics_agent import SYSTEM_PROMPT as LOGISTICS_PROMPT
    from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
    from backend.agents.finance_agent import SYSTEM_PROMPT as FINANCE_PROMPT
    from backend.agents.brand_agent import SYSTEM_PROMPT as BRAND_PROMPT

    AGENT_PROMPTS_MAP = {
        "risk": RISK_PROMPT, "supply": SUPPLY_PROMPT, "logistics": LOGISTICS_PROMPT,
        "market": MARKET_PROMPT, "finance": FINANCE_PROMPT, "brand": BRAND_PROMPT,
    }

    query = state.get("query", "")
    context = state.get("context") or {}
    primary_agent = state.get("primary_agent") or context.get("primary_agent", "risk")
    evidence_bundle = state.get("evidence_bundle")

    system_prompt = AGENT_PROMPTS_MAP.get(primary_agent, RISK_PROMPT)
    system_content = (
        system_prompt
        + "\n\nLITE MODE PRIMARY TASK:\n"
        + "You are the single final decision-maker. Use all support evidence, merge contradictions, "
        + "and deliver the best final answer. Do not debate other agents. "
        + "Synthesize the evidence into one clean recommendation.\n"
    )

    messages = [{"role": "system", "content": system_content}]

    # Inject MCP tool descriptions
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt
        messages = inject_mcp_system_prompt(messages, primary_agent)
    except Exception:
        pass

    # Inject RAG context for primary agent
    rag_contexts = context.get("rag_contexts") or {}
    primary_rag = rag_contexts.get(primary_agent, "")
    if primary_rag:
        messages.append({"role": "system", "content": primary_rag})

    # Inject evidence bundle
    if evidence_bundle:
        support_summary = "\n".join(
            f"**{e['agent']}** (confidence {e['confidence']}%): {e['summary'][:300]}"
            for e in evidence_bundle.get("support_evidence", [])
        )
        data_quality = evidence_bundle.get("data_quality_summary", "Unknown")
        conflicts = evidence_bundle.get("conflicts", [])
        messages.append({
            "role": "system",
            "content": (
                f"## Merged Evidence Bundle\n"
                f"Data Quality: {data_quality}\n"
                f"Conflicts: {', '.join(conflicts) if conflicts else 'None'}\n\n"
                f"### Support Agent Evidence:\n{support_summary}"
            ),
        })

    # Inject subagent evidence if available
    subagent_evidence = state.get("subagent_evidence", [])
    if subagent_evidence:
        from backend.state import SubagentEvidence
        subagent_summary = "\n\n".join(
            f"**{se.get('data_channel', '').upper()}** (confidence {se.get('confidence', 0)}%): {se.get('summary', '')[:300]}"
            for se in subagent_evidence
        )
        messages.append({
            "role": "system",
            "content": f"## Subagent Evidence (5 hybrid researchers):\n{subagent_summary}",
        })

    messages.append({
        "role": "user",
        "content": (
            f"Primary agent: {primary_agent}\n"
            f"Original query: {query}\n\n"
            "Now synthesize the final answer using the evidence above. "
            "State the conclusion clearly, include citations inline, and provide a confidence score."
        ),
    })

    try:
        response, model_used = await llm_router.invoke_with_fallback(primary_agent, messages)
        recommendation = response.content
    except Exception as e:
        logger.error(f"Primary synthesis LLM call failed: {e}")
        recommendation = f"Primary synthesis failed: {e}"

    # Parse confidence and risk
    import re as _re
    confidence = 50.0
    for p in [r"confidence[:\s]+(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)\s*/\s*100", r"(\d+(?:\.\d+)?)\s*%\s*confidence"]:
        m = _re.search(p, recommendation, _re.IGNORECASE)
        if m:
            v = float(m.group(1))
            confidence = min(v, 100.0) if v > 1 else v * 100
            break

    risk_score = 50.0
    for p in [r"risk\s+score[:\s]+(\d+(?:\.\d+)?)", r"risk[:\s]+(\d+(?:\.\d+)?)"]:
        m = _re.search(p, recommendation, _re.IGNORECASE)
        if m:
            v = float(m.group(1))
            risk_score = min(v, 100.0) if v > 1 else v * 100
            break

    logger.info(f"Primary synthesis complete: confidence={confidence:.0f}, risk={risk_score:.0f}")
    return {
        "recommendation": recommendation,
        "confidence": confidence / 100.0,
        "risk_score": risk_score,
    }


# ---------------------------------------------------------------------------
# Lite Mode: Conditional edge — which agents should run in lite mode
# ---------------------------------------------------------------------------
def _lite_agent_fanout(state: CouncilState):
    """Fan-out for lite mode: primary agent + 5 support agents."""
    ctx = state.get("context") or {}
    primary_agent = state.get("primary_agent") or ctx.get("primary_agent", "risk")
    active_agents = ctx.get("active_agents") or AGENT_KEYS
    targets = []
    for name in active_agents:
        if name in AGENT_KEYS:
            targets.append(Send(name, state))
    if not targets:
        targets.append(Send("risk", state))
    return targets


# ---------------------------------------------------------------------------
# Build the lite-mode council graph
# ---------------------------------------------------------------------------
def build_lite_council_graph() -> StateGraph:
    """Build a streamlined graph for lite mode.

    Flow: moderator → dynamic_routing → rag_prefetch → mcp_escalation
          → agent fan-out → evidence_merge → primary_synthesis → END

    Skips: debate, fallback, brand_enhancement, moderator_synthesize
    """
    graph = StateGraph(CouncilState)

    # Add nodes
    graph.add_node("moderator", moderator_parse)
    graph.add_node("dynamic_routing", dynamic_routing_node)
    graph.add_node("rag_prefetch", rag_prefetch)
    graph.add_node("mcp_escalation", mcp_escalation)
    graph.add_node("risk", risk_agent)
    graph.add_node("supply", supply_agent)
    graph.add_node("logistics", logistics_agent)
    graph.add_node("market", market_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("brand", brand_agent)
    graph.add_node("evidence_merge", evidence_merge_node)
    graph.add_node("primary_synthesis", primary_synthesis_node)

    graph.set_entry_point("moderator")

    # Phase 1: Moderator → Dynamic Routing → RAG → MCP → Agent fan-out
    graph.add_edge("moderator", "dynamic_routing")
    graph.add_edge("dynamic_routing", "rag_prefetch")
    graph.add_edge("rag_prefetch", "mcp_escalation")

    # Single conditional edge for all agents
    graph.add_conditional_edges("mcp_escalation", _lite_agent_fanout, [
        "risk", "supply", "logistics", "market", "finance", "brand"
    ])

    # Phase 2: All agents converge to evidence merge
    for agent in ["risk", "supply", "logistics", "market", "finance", "brand"]:
        graph.add_edge(agent, "evidence_merge")

    # Phase 3: Evidence merge → Primary synthesis → END
    graph.add_edge("evidence_merge", "primary_synthesis")
    graph.add_edge("primary_synthesis", END)

    return graph


# ---------------------------------------------------------------------------
# Day 6: Human-in-the-loop interrupt node
# ---------------------------------------------------------------------------
async def human_review_node(state: CouncilState) -> dict:
    """Interrupt point for human review before final synthesis.

    When settings.human_in_loop is True, the graph pauses here
    and waits for human_approved to be set in the state before
    proceeding to synthesis.

    This node is NOT added to the graph by default — it is used
    by the streaming runner which checks the flag and injects it.
    """
    human_approved = state.get("human_approved")
    if human_approved is None:
        # Mark that we're waiting for human input
        logger.info(f"Human review requested for session {state.get('session_id')}")
        return {"human_approved": False}  # Will be overridden by human input
    return {}


# ---------------------------------------------------------------------------
# Day 6: Streaming runner — yields intermediate debate results via callback
# ---------------------------------------------------------------------------
async def run_council_streaming(
    query: str,
    context: dict | None = None,
    session_id: str | None = None,
    ws_callback=None,
):
    """Run the full council graph with streaming support.

    Yields intermediate results as they complete:
      - Each agent output as it finishes
      - Each debate round as it completes
      - Final recommendation

    Args:
        query: The supply chain query
        context: Optional context dict
        session_id: Optional session ID (auto-generated if not provided)
        ws_callback: Optional async callable(payload: dict) for WebSocket push

    Yields:
        dict with {type, data} for each intermediate result
    """
    import uuid
    if not session_id:
        session_id = str(uuid.uuid4())

    from backend.observability.langsmith_config import CouncilTracer, record_agent_call
    tracer = CouncilTracer(session_id)

    initial_state = {
        "query": query,
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
        "session_id": session_id,
        "context": context or {},
        "debate_rounds": [],
        "predictions": [],
        "tiered_fallbacks": [],
        "brand_sentiment": None,
        "human_approved": None,
        # Lite Mode fields
        "lite_mode": (context or {}).get("lite_mode", False),
        "primary_agent": (context or {}).get("primary_agent"),
        "support_evidence": [],
        "evidence_bundle": None,
        "subagent_evidence": [],
        # Astra ⭐ Integration
        "astra_results": None,
    }

    is_lite = initial_state["lite_mode"]
    if is_lite:
        graph = build_lite_council_graph()
    else:
        graph = build_council_graph()

    # Use interrupt_before if human-in-loop is enabled
    compile_kwargs = {}
    if settings.human_in_loop:
        compile_kwargs["interrupt_before"] = ["synthesize"]

    compiled = graph.compile(**compile_kwargs)

    # Stream events from the graph — track final state for Redis
    final_state = initial_state
    async for event in compiled.astream_events(initial_state, version="v2"):
        kind = event.get("event", "")

        # Track state updates
        if kind == "on_chain_end" and event.get("data", {}).get("output"):
            node_name = event.get("name", "")
            output = event["data"]["output"]
            if isinstance(output, dict):
                final_state = {**final_state, **output}

            if node_name in ("risk", "supply", "logistics", "market", "finance", "brand"):
                payload = {
                    "type": "agent_done",
                    "data": {
                        "agent": node_name,
                        "session_id": session_id,
                    },
                }
                if isinstance(output, dict) and "agent_outputs" in output:
                    for ao in output.get("agent_outputs", []):
                        payload["data"]["confidence"] = ao.confidence if hasattr(ao, "confidence") else 0
                        payload["data"]["contribution"] = ao.contribution[:200] if hasattr(ao, "contribution") else ""

                yield payload
                if ws_callback:
                    try:
                        await ws_callback(payload)
                    except Exception:
                        pass

            elif node_name == "astra_parallel":
                # ⭐ Stream Astra simulation results
                astra_results = output.get("astra_results")
                if astra_results:
                    payload = {
                        "type": "astra_results",
                        "data": {
                            "session_id": session_id,
                            "astra_results": astra_results,
                            "brand_status": astra_results.get("brand", {}).get("status", "unknown"),
                            "market_status": astra_results.get("market", {}).get("status", "unknown"),
                        },
                    }
                    yield payload
                    if ws_callback:
                        try:
                            await ws_callback(payload)
                        except Exception:
                            pass

            elif node_name == "debate":
                payload = {
                    "type": "debate_round",
                    "data": {
                        "session_id": session_id,
                        "debate_rounds": output.get("debate_rounds", []),
                        "confidence": output.get("confidence", 0),
                        "risk_score": output.get("risk_score", 0),
                    },
                }
                yield payload
                if ws_callback:
                    try:
                        await ws_callback(payload)
                    except Exception:
                        pass

            elif node_name == "evidence_merge":
                payload = {
                    "type": "evidence_bundle",
                    "data": {
                        "session_id": session_id,
                        "evidence_bundle": output.get("evidence_bundle"),
                        "support_evidence": output.get("support_evidence", []),
                    },
                }
                yield payload
                if ws_callback:
                    try:
                        await ws_callback(payload)
                    except Exception:
                        pass

            elif node_name == "primary_synthesis":
                payload = {
                    "type": "complete",
                    "data": {
                        "session_id": session_id,
                        "recommendation": output.get("recommendation", ""),
                        "confidence": output.get("confidence", 0),
                        "risk_score": output.get("risk_score", 0),
                        "lite_mode": True,
                        "primary_agent": initial_state.get("primary_agent"),
                    },
                }
                yield payload
                if ws_callback:
                    try:
                        await ws_callback(payload)
                    except Exception:
                        pass

            elif node_name == "synthesize":
                payload = {
                    "type": "complete",
                    "data": {
                        "session_id": session_id,
                        "recommendation": output.get("recommendation", ""),
                        "confidence": output.get("confidence", 0),
                        "risk_score": output.get("risk_score", 0),
                    },
                }
                yield payload
                if ws_callback:
                    try:
                        await ws_callback(payload)
                    except Exception:
                        pass

    # Store session to Redis using tracked state — no double execution
    try:
        from backend.db.redis_client import cache_set
        session_data = {
            "session_id": session_id,
            "query": query,
            "recommendation": final_state.get("recommendation", ""),
            "confidence": final_state.get("confidence", 0),
            "risk_score": final_state.get("risk_score", 0),
            "debate_rounds": final_state.get("debate_rounds", []),
            "agent_outputs": [
                {"agent": o.agent, "confidence": o.confidence, "contribution": o.contribution[:300]}
                for o in final_state.get("agent_outputs", [])
            ],
            "timestamp": time.time(),
            "lite_mode": final_state.get("lite_mode", False),
            "primary_agent": final_state.get("primary_agent"),
            "evidence_bundle": final_state.get("evidence_bundle"),
            "astra_results": final_state.get("astra_results"),  # ⭐ Include Astra results
        }
        await cache_set(f"council_session:{session_id}", session_data, ttl=settings.session_store_ttl)
    except Exception as e:
        logger.warning(f"Session storage to Redis failed: {e}")
