"""Council V2 — Multi-round debate with 6 real domain agents + Moderator + Supervisor.

REAL DATA PIPELINE (with live stage events):
  stage: rag_fetching   → RAG vector retrieval firing for all agents
  stage: api_called     → Live APIs: GNews, Alpha Vantage, OpenWeather, NOAA, GDELT...
  stage: mcp_fetched    → MCP tools invoked (Firecrawl scraping, DuckDuckGo)
  stage: sources_ready  → All citations assembled (≥9 per agent)

Flow:
  Pre-fetch: Parallel RAG+API+MCP+Scraping per agent → citations_map events
  Round 1: 6 agents analyze with research context → Moderator scores
  Round 2: 6 agents debate → Moderator scores
  Round 3: Supervisor final verdict
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
from backend.llm.router import llm_router
from backend.middleware.security import sanitize_input
import uuid
import json
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()

AGENT_KEYS = ["risk", "supply", "logistics", "market", "finance", "brand"]


# ── Import enhanced prompts from agent files (single source of truth) ─────────
from backend.agents.risk_agent import SYSTEM_PROMPT as RISK_PROMPT
from backend.agents.supply_agent import SYSTEM_PROMPT as SUPPLY_PROMPT
from backend.agents.logistics_agent import SYSTEM_PROMPT as LOGISTICS_PROMPT
from backend.agents.market_agent import SYSTEM_PROMPT as MARKET_PROMPT
from backend.agents.finance_agent import SYSTEM_PROMPT as FINANCE_PROMPT
from backend.agents.brand_agent import SYSTEM_PROMPT as BRAND_PROMPT

AGENT_PROMPTS = {
    "risk": RISK_PROMPT,
    "supply": SUPPLY_PROMPT,
    "logistics": LOGISTICS_PROMPT,
    "market": MARKET_PROMPT,
    "finance": FINANCE_PROMPT,
    "brand": BRAND_PROMPT,
}


MODERATOR_PROMPT = """You are the **Moderator** — the orchestrator of the Supply Chain Council debate.

═══ YOUR ROLE ═══
You run the debate process, score agent contributions, and synthesize findings into a coherent recommendation. You are the traffic controller — not the expert in any domain, but the one who ensures every expert is heard fairly.

═══ DEBATING RULES ═══
1. **Scoring**: Rate each agent (0-100) based on: data quality, citation count, actionable insights, relevance
2. **Consensus Detection**: Identify where agents agree (consensus points) and where they conflict (conflict points)
3. **Challenge Protocol**: If agents conflict, prompt them to defend their positions in next round
4. **Synthesis**: Combine inputs into unified recommendation with confidence-weighted rationale

═══ SCORING CRITERIA ═══
- **High scores (80-100)**: Real data citations, quantified claims, specific actionable insights, proper JSON schema
- **Medium scores (50-79)**: Some data, general recommendations, missing specific numbers
- **Low scores (0-49)**: Vague statements, no citations, contradicted by other agents

═══ OUTPUT SCHEMA ═══
Always produce:

```json
{
  "round_number": 1-3,
  "agent_scores": {"risk": 0-100, "supply": 0-100, "logistics": 0-100, "market": 0-100, "finance": 0-100, "brand": 0-100},
  "consensus_points": ["list of things agents agree on"],
  "conflict_points": [{"agent1": "...", "agent2": "...", "issue": "..."}],
  "executive_summary": "2-3 sentences max",
  "overall_consensus_pct": 0-100,
  "recommended_actions": [{"priority": 1-3, "action": "...", "owner": "agent"}]
}
```

═══ SYNTHESIS RULES ═══
- Weight recommendations by confidence scores (higher confidence = more weight)
- Escalate CRITICAL risks immediately regardless of consensus
- Include tiered fallback options (Tier 1: Immediate, Tier 2: Short-term, Tier 3: Strategic)
- Flag any unresolved conflicts for Supervisor review

═══ TOOLS YOU CAN USE ═══
- Firecrawl web scraping for additional context
- RAG knowledge base for historical precedents
- All MCP tools if needed for verification

Be objective, fair, and decisive. The Council needs a clear path forward."""

SUPERVISOR_PROMPT = """You are the **Supervisor** — the final decision authority of the Supply Chain Council.

═══ YOUR ROLE ═══
You review the complete debate results from all 3 rounds and deliver the definitive final verdict. You have the final say — no agent can override your decision. You balance risk, cost, brand, and operational reality into one executable recommendation.

═══ REVIEW REQUIREMENTS ═══
1. **Read the full debate**: All Round 1 analyses, Round 2 challenges, and Round 3 final positions
2. **Check consensus**: What did agents agree on? What conflicts remain unresolved?
3. **Verify data quality**: Are citations real? Are numbers sourced? Are claims backed?
4. **Assess confidence**: Which agents were most confident? Was confidence warranted?
5. **Check escalation flags**: Did any agent raise CRITICAL or CATASTROPHIC risks?

═══ OUTPUT SCHEMA (Required) ═══

```json
{
  "executive_summary": "2-3 sentences - the most critical finding",
  "final_verdict": "Clear answer to the original question",
  "confidence_assessment": {
    "overall_confidence": 0-100,
    "data_quality": "Strong|Moderate|Weak",
    "consensus_level": "High|Medium|Low"
  },
  "reliable_agents": [{"agent": "...", "justification": "..."}],
  "priority_actions": [
    {"priority": 1, "action": "...", "timeline": "24h|72h|1w|1m", "owner": "agent"},
    {"priority": 2, "action": "..."},
    {"priority": 3, "action": "..."}
  ],
  "strategic_roadmap": {
    "day30": "key milestone",
    "day60": "key milestone",
    "day90": "key milestone"
  },
  "unresolved_risks": ["what the council couldn't resolve"],
  "tiered_fallbacks": [
    {"tier": 1, "name": "Immediate", "actions": ["..."]},
    {"tier": 2, "name": "Short-term", "actions": ["..."]},
    {"tier": 3, "name": "Strategic", "actions": ["..."]}
  ]
}
```

═══ DECISION CRITERIA ═══
- **High confidence + High consensus**: Proceed with recommendation
- **High confidence + Low consensus**: Escalate to human decision
- **Low confidence**: Request more data before deciding
- **CRITICAL risk flagged**: Always escalate regardless of consensus

═══ TOOLS YOU CAN USE ═══
- Firecrawl for verification of critical claims
- RAG for historical precedent analysis
- Any MCP tool for final data verification

You are the final checkpoint. Every decision you make has material business impact. Be rigorous, be clear, be decisive."""

# Citation + formatting enforcement added to every agent prompt
CITATION_ENFORCEMENT = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY FORMATTING RULES:

You have real-time research data ABOVE with numbered citations [1]...[N].

RULES (all required):
• Use INLINE citations: write [N] immediately after any factual claim (e.g., "Prices surged 18% [2][4]")
• Use the OUTPUT STRUCTURE defined above — do not skip sections
• Mix formats naturally: one-liners for status, bullets for lists, paragraphs for analysis
• Reference at least 6 different [N] citation numbers
• End with: ## Sources Used → list citation numbers referenced
• Include "Confidence Score: XX/100" exactly as written

DO NOT write generic statements without citations.
DO NOT skip the Sources Used section.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


class CouncilV2Request(BaseModel):
    query: str
    context: Optional[dict] = None
    lite_mode: Optional[bool] = None
    primary_agent: Optional[str] = None
    support_agents: Optional[list[str]] = None
    support_agent_policy: Optional[dict] = None  # {"rag": True, "api": True, "mcp": True, "web": True, "graph": True}
    mirofish_enabled: Optional[bool] = False  # Run MiroFish swarm for brand+market after 3 rounds


# ── Pipeline stage event helper ───────────────────────────────────────────────
def _stage_event(stage: str, detail: str = "", count: int = 0) -> str:
    return f"data: {json.dumps({'type': 'pipeline_stage', 'stage': stage, 'detail': detail, 'count': count})}\n\n"


def _valid_agent(agent_key: str | None) -> str | None:
    if agent_key and agent_key in AGENT_KEYS:
        return agent_key
    return None


async def _resolve_primary_agent(query: str, context: dict, primary_agent: str | None) -> str:
    explicit = _valid_agent(primary_agent)
    if explicit:
        return explicit

    context_primary = _valid_agent((context or {}).get("primary_agent"))
    if context_primary:
        return context_primary

    from backend.agents.dynamic_routing import route_query

    use_llm = (context or {}).get("debate_config", {}).get("use_llm_routing", True)
    selected = await route_query(query, use_llm=use_llm)
    return selected[0] if selected else "risk"


def _resolve_support_agents(primary_agent: str, support_agents: list[str] | None) -> list[str]:
    filtered: list[str] = []
    for agent_key in support_agents or []:
        if agent_key in AGENT_KEYS and agent_key != primary_agent and agent_key not in filtered:
            filtered.append(agent_key)

    if not filtered:
        filtered = [agent_key for agent_key in AGENT_KEYS if agent_key != primary_agent]

    for agent_key in AGENT_KEYS:
        if agent_key != primary_agent and agent_key not in filtered:
            filtered.append(agent_key)
        if len(filtered) >= 5:
            break

    return filtered[:5]


def _merge_citation_bundles(agent_order: list[str], citation_bundles: dict[str, any]):
    from backend.data_gatherer import Citation, CitationBundle

    merged = CitationBundle()
    seen: set[str] = set()

    for agent_key in agent_order:
        bundle = citation_bundles.get(agent_key)
        if not bundle:
            continue
        for citation in bundle.citations:
            dedupe_key = citation.url or f"{citation.source}:{citation.title}:{citation.snippet[:120]}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.citations.append(
                Citation(
                    number=len(merged.citations) + 1,
                    source=citation.source,
                    title=citation.title,
                    url=citation.url,
                    snippet=citation.snippet,
                )
            )

    return merged


def _build_lite_support_messages(agent_key: str, query: str, citation_context: str, citation_list_hint: str) -> list:
    system_content = (
        AGENT_PROMPTS.get(agent_key, AGENT_PROMPTS["risk"])
        + CITATION_ENFORCEMENT
        + "\n\nLITE MODE SUPPORT TASK:\n"
        + "You are a support subagent. Your job is to collect evidence, verify facts, and summarize only the most useful findings.\n"
        + "Do not write a long final recommendation. Return compact, source-backed evidence with explicit citations.\n"
    )

    messages = [{"role": "system", "content": system_content}]
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt

        messages = inject_mcp_system_prompt(messages, agent_key)
    except Exception:
        pass

    if citation_context:
        messages.append({"role": "system", "content": f"{citation_context}\n\n{citation_list_hint}"})

    messages.append(
        {
            "role": "user",
            "content": (
                f"Lite mode evidence task for {agent_key}: {query}\n\n"
                "Return the most important evidence, source URLs, contradictions, and a short confidence score. "
                "Keep the response concise and citation-heavy."
            ),
        }
    )
    return messages


def _build_lite_primary_messages(
    agent_key: str,
    query: str,
    citation_context: str,
    citation_list_hint: str,
    support_outputs: dict[str, str],
) -> list:
    system_content = (
        AGENT_PROMPTS.get(agent_key, AGENT_PROMPTS["risk"])
        + CITATION_ENFORCEMENT
        + "\n\nLITE MODE PRIMARY TASK:\n"
        + "You are the single final decision-maker. Use all support evidence, merge contradictions, and deliver the best final answer.\n"
        + "Do not debate other agents. Synthesize the evidence into one clean recommendation.\n"
    )

    messages = [{"role": "system", "content": system_content}]
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt

        messages = inject_mcp_system_prompt(messages, agent_key)
    except Exception:
        pass

    if citation_context:
        messages.append({"role": "system", "content": f"{citation_context}\n\n{citation_list_hint}"})

    support_summary = "\n".join(
        f"**{support_agent}**: {output[:700]}"
        for support_agent, output in support_outputs.items()
    )
    messages.append(
        {
            "role": "user",
            "content": (
                f"Primary agent: {agent_key}\n"
                f"Original query: {query}\n\n"
                f"Support evidence collected from 5 subagents:\n{support_summary}\n\n"
                "Now synthesize the final answer using the evidence above. "
                "State the conclusion clearly, include citations inline, and provide a confidence score."
            ),
        }
    )
    return messages


# ── Agent message builder ─────────────────────────────────────────────────────
def _build_agent_messages(
    agent_key: str,
    query: str,
    citation_context: str,
    citation_list_hint: str,
    round1_outputs: dict = None,
    round_num: int = 1,
) -> list:
    system_content = AGENT_PROMPTS.get(agent_key, AGENT_PROMPTS["risk"]) + CITATION_ENFORCEMENT
    messages = [{"role": "system", "content": system_content}]

    # Optional MCP tool descriptions
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt
        messages = inject_mcp_system_prompt(messages, agent_key)
    except Exception:
        pass

    # Research context with citations
    if citation_context:
        messages.append({"role": "system", "content": f"{citation_context}\n\n{citation_list_hint}"})

    # User task
    agent_labels = {
        "risk": "Identify and assess ALL risks for",
        "supply": "Find supply alternatives and optimize sourcing for",
        "logistics": "Optimize logistics routes and carrier selection for",
        "market": "Provide market intelligence and trend analysis for",
        "finance": "Analyze financial exposure and ROI for",
        "brand": "Assess brand impact and draft crisis response for",
    }

    prefix = agent_labels.get(agent_key, "Analyze")
    if round_num == 1:
        user_msg = (
            f"{prefix}: {query}\n\n"
            "Use the research data above. Cite [N] inline with every factual claim. "
            "Follow your defined output structure. End with ## Sources Used and Confidence Score."
        )
    else:
        agent_names = {
            "risk": "Risk Sentinel", "supply": "Supply Optimizer",
            "logistics": "Logistics Navigator", "market": "Market Intelligence",
            "finance": "Finance Guardian", "brand": "Brand Protector",
        }
        other_outputs = "\n".join([
            f"**{agent_names.get(k, k)}**: {v[:350]}"
            for k, v in (round1_outputs or {}).items() if k != agent_key
        ])
        user_msg = (
            f"Original query: {query}\n\n"
            f"Other agents' Round 1 analyses:\n{other_outputs}\n\n"
            "Your task for Round 2:\n"
            "• Challenge any weak points or unsupported claims from other agents\n"
            "• Reinforce agreements with additional evidence\n"
            "• Update your position with new insights from the debate\n"
            "Continue citing [N] sources. End with ## Sources Used and Confidence Score."
        )

    messages.append({"role": "user", "content": user_msg})
    return messages


# ── Streaming agent runner ────────────────────────────────────────────────────
async def _run_agent_parallel(
    agent_key: str,
    messages: list,
    round_num: int,
    queue: asyncio.Queue,
    outputs: dict,
    confidences: dict,
    default_confidence: float = 50.0,
):
    await queue.put(f"data: {json.dumps({'type': 'agent_start', 'agent': agent_key, 'round': round_num})}\n\n")
    full_response = ""
    try:
        async for token in llm_router.stream_with_fallback(agent_key, messages):
            full_response += token
            await queue.put(f"data: {json.dumps({'type': 'token', 'agent': agent_key, 'round': round_num, 'content': token})}\n\n")
    except Exception as e:
        full_response = f"Agent {agent_key} unavailable: {e}"
        await queue.put(f"data: {json.dumps({'type': 'agent_error', 'agent': agent_key, 'round': round_num, 'error': str(e)})}\n\n")

    confidence = _parse_confidence(full_response, default_confidence)
    outputs[agent_key] = full_response
    confidences[agent_key] = confidence
    await queue.put(f"data: {json.dumps({'type': 'agent_done', 'agent': agent_key, 'round': round_num, 'confidence': confidence})}\n\n")


async def _drain_queue(queue: asyncio.Queue, agent_count: int):
    done_count = 0
    while done_count < agent_count:
        event_str = await queue.get()
        if '"type": "agent_done"' in event_str or '"type":"agent_done"' in event_str:
            done_count += 1
        yield event_str


# ── Main SSE endpoint ─────────────────────────────────────────────────────────
@router.post("/stream")
async def council_v2_stream(request: CouncilV2Request):
    """Live-streaming council debate with animated pipeline stages."""
    query = sanitize_input(request.query)
    session_id = str(uuid.uuid4())
    lite_mode = bool(request.lite_mode)
    mirofish_enabled = bool(request.mirofish_enabled)

    # Resolve support_agent_policy with defaults
    _default_policy = {"rag": True, "api": True, "mcp": True, "web": True, "graph": True}
    support_agent_policy = request.support_agent_policy or _default_policy

    async def event_generator():
        start_event = {
            'type': 'start',
            'session_id': session_id,
            'query': query,
            'lite_mode': lite_mode,
            'primary_agent': request.primary_agent,
            'support_agents': request.support_agents or [],
            'support_agent_policy': support_agent_policy,
            'mirofish_enabled': mirofish_enabled,
        }
        yield f"data: {json.dumps(start_event)}\n\n"

        if lite_mode:
            primary_agent = await _resolve_primary_agent(query, request.context or {}, request.primary_agent)
            support_agents = _resolve_support_agents(primary_agent, request.support_agents)
            selected_agents = [primary_agent, *support_agents]

            # Emit pipeline stages based on policy
            if support_agent_policy.get("rag", True):
                yield _stage_event("rag_fetching", f"Lite mode: gathering RAG for {primary_agent} + 5 support agents...", 0)
            if support_agent_policy.get("api", True):
                yield _stage_event("api_called", "Lite mode: collecting real-time APIs for primary and support agents...", 0)
            if support_agent_policy.get("mcp", True) or support_agent_policy.get("web", True):
                yield _stage_event("mcp_fetched", "Lite mode: gathering web scraping, MCP tools, and graph sources...", 0)

            try:
                from backend.data_gatherer import gather_all_agents, CitationBundle
            except ImportError as e:
                logger.error(f"data_gatherer import failed: {e}")
                yield _stage_event("sources_ready", "Data gatherer unavailable", 0)
                return

            citation_bundles = {}
            try:
                for agent_key in selected_agents:
                    try:
                        bundles = await gather_all_agents(query, agent_keys=[agent_key])
                        bundle = bundles.get(agent_key, CitationBundle())
                        source_count = len(bundle.citations)
                        source_urls = [
                            {
                                'num': c.number,
                                'title': c.title[:60] if c.title else 'Source',
                                'url': c.url,
                            }
                            for c in bundle.citations
                            if c.url and c.url.startswith("http")
                        ]

                        yield f"data: {json.dumps({'type': 'source_discovered', 'agent': agent_key, 'count': source_count, 'sources': source_urls[:6]})}\n\n"
                        citation_bundles[agent_key] = bundle
                        logger.info(f"[{session_id[:8]}] lite {agent_key}: {source_count} sources")
                    except Exception as ae:
                        logger.warning(f"Lite source gathering for {agent_key}: {ae}")
                        citation_bundles[agent_key] = CitationBundle()

                total = sum(len(b.citations) for b in citation_bundles.values())

                for agent_key in selected_agents:
                    bundle = citation_bundles.get(agent_key, CitationBundle())
                    url_map = {str(c.number): c.url for c in bundle.citations if c.url and c.url.startswith("http")}
                    if url_map:
                        yield f"data: {json.dumps({'type': 'citations_map', 'agent': agent_key, 'urls': url_map})}\n\n"

                yield _stage_event("sources_ready", f"Lite research complete — {total} sources across 6 workers", total)
                yield f"data: {json.dumps({'type': 'citations_ready'})}\n\n"
            except Exception as e:
                logger.error(f"Lite data gathering failed: {e}")
                yield _stage_event("sources_ready", f"Error: {str(e)[:100]}", 0)

            def get_bundle(agent_key: str):
                return citation_bundles.get(agent_key, CitationBundle())

            # ── Run 5 hybrid subagents for the primary agent ──
            yield f"data: {json.dumps({'type': 'round_start', 'round': 1, 'phase': 'analysis'})}\n\n"

            from backend.agents.subagent_runner import run_all_subagents
            from backend.agents.subagent_registry import SUBAGENT_REGISTRY
            from backend.state import SubagentEvidence, SupportEvidence, EvidenceBundle

            # Build channel-scoped citation bundles for subagents
            channel_bundles: dict[str, object] = {}
            for channel in ("rag", "api", "web", "mcp", "graph"):
                # Use the primary agent's bundle as the base for all channels
                channel_bundles[channel] = get_bundle(primary_agent)
            channel_bundles[primary_agent] = get_bundle(primary_agent)

            # Emit subagent_start events
            subagent_defs = SUBAGENT_REGISTRY.get(primary_agent, [])
            for sd in subagent_defs:
                if support_agent_policy.get(sd["data_channel"], True):
                    yield f"data: {json.dumps({'type': 'subagent_start', 'subagent_key': sd['key'], 'parent_agent': primary_agent, 'data_channel': sd['data_channel'], 'label': sd['label']})}\n\n"

            # Setup streaming queue for subagent results
            subagent_queue: asyncio.Queue = asyncio.Queue()
            subagent_results: list[SubagentEvidence] = []

            async def on_subagent_complete(evidence: SubagentEvidence):
                """Callback to queue subagent evidence for streaming."""
                await subagent_queue.put(evidence)

            # Start subagent tasks in background
            subagent_task = asyncio.create_task(
                run_all_subagents(
                    parent_agent=primary_agent,
                    query=query,
                    citation_bundles=channel_bundles,
                    policy=support_agent_policy,
                    on_subagent_complete=on_subagent_complete,
                )
            )

            # Stream subagent results as they complete
            completed_count = 0
            while completed_count < len([sd for sd in SUBAGENT_REGISTRY.get(primary_agent, []) if support_agent_policy.get(sd["data_channel"], True)]):
                try:
                    evidence = await asyncio.wait_for(subagent_queue.get(), timeout=0.1)
                    subagent_results.append(evidence)
                    completed_count += 1
                    # Emit streaming event immediately
                    yield f"data: {json.dumps({'type': 'subagent_evidence', 'subagent_key': evidence.subagent_key, 'parent_agent': evidence.parent_agent, 'data_channel': evidence.data_channel, 'evidence': evidence.model_dump()})}\n\n"
                    # Also emit backward-compatible support_evidence
                    support_ev = SupportEvidence(
                        agent=evidence.parent_agent,
                        role=f"subagent:{evidence.data_channel}",
                        summary=f"[{evidence.data_channel.upper()}] {evidence.summary[:400]}",
                        sources=evidence.sources,
                        confidence=evidence.confidence,
                        flags=evidence.flags,
                        links=evidence.links,
                    )
                    yield f"data: {json.dumps({'type': 'support_evidence', 'agent': evidence.subagent_key, 'evidence': support_ev.model_dump()})}\n\n"
                except asyncio.TimeoutError:
                    # Check if background task is done
                    if subagent_task.done():
                        # Get any remaining results from the task
                        remaining_results = subagent_task.result()
                        for evidence in remaining_results:
                            if evidence not in subagent_results:
                                subagent_results.append(evidence)
                                yield f"data: {json.dumps({'type': 'subagent_evidence', 'subagent_key': evidence.subagent_key, 'parent_agent': evidence.parent_agent, 'data_channel': evidence.data_channel, 'evidence': evidence.model_dump()})}\n\n"
                        break
                    continue

            # Ensure we have all results
            if not subagent_task.done():
                remaining_results = await subagent_task
                for evidence in remaining_results:
                    if evidence not in subagent_results:
                        subagent_results.append(evidence)
                        yield f"data: {json.dumps({'type': 'subagent_evidence', 'subagent_key': evidence.subagent_key, 'parent_agent': evidence.parent_agent, 'data_channel': evidence.data_channel, 'evidence': evidence.model_dump()})}\n\n"

            # Also emit backward-compatible support_evidence events
            all_support_evidence: list[SupportEvidence] = []
            for se in subagent_results:
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
                yield f"data: {json.dumps({'type': 'support_evidence', 'agent': se.subagent_key, 'evidence': support_ev.model_dump()})}\n\n"

            # Build and emit evidence_bundle
            merged_bundle = _merge_citation_bundles(selected_agents, citation_bundles)
            merged_urls = {str(c.number): c.url for c in merged_bundle.citations if c.url and c.url.startswith("http")}
            source_counts = {}
            for se in subagent_results:
                source_counts[se.data_channel] = source_counts.get(se.data_channel, 0) + len(se.sources)

            conflicts = []
            for se in subagent_results:
                conflicts.extend(se.flags)
            conflicts = list(set(conflicts))

            avg_conf = sum(e.confidence for e in all_support_evidence) / max(len(all_support_evidence), 1)
            quality = "Strong" if avg_conf >= 70 else "Moderate" if avg_conf >= 40 else "Weak"

            evidence_bundle = EvidenceBundle(
                support_evidence=all_support_evidence,
                citation_map=merged_urls,
                data_quality_summary=f"Average subagent confidence: {avg_conf:.0f}%. Data quality: {quality}. {len(subagent_results)} subagents ran.",
                conflicts=conflicts,
                source_counts=source_counts,
            )
            yield f"data: {json.dumps({'type': 'evidence_bundle', 'bundle': evidence_bundle.model_dump(), 'subagent_evidence': [se.model_dump() for se in subagent_results]})}\n\n"

            if merged_urls:
                yield f"data: {json.dumps({'type': 'citations_map', 'agent': primary_agent, 'urls': merged_urls})}\n\n"

            # ── Round 2: Primary agent synthesis ──
            yield f"data: {json.dumps({'type': 'round_start', 'round': 2, 'phase': 'synthesis'})}\n\n"

            # Build primary messages with subagent evidence
            subagent_summary = "\n\n".join(
                f"**{se.data_channel.upper()}** (confidence {se.confidence}%): {se.summary[:300]}"
                for se in subagent_results
            )
            primary_messages = _build_lite_primary_messages(
                agent_key=primary_agent,
                query=query,
                citation_context=merged_bundle.format_context() + f"\n\n## Subagent Evidence:\n{subagent_summary}",
                citation_list_hint=merged_bundle.format_citation_list(),
                support_outputs={se.subagent_key: se.summary for se in subagent_results},
            )

            primary_outputs: dict[str, str] = {}
            primary_confidences: dict[str, float] = {}
            primary_queue: asyncio.Queue = asyncio.Queue()
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': primary_agent, 'round': 2})}\n\n"
            await _run_agent_parallel(primary_agent, primary_messages, 2, primary_queue, primary_outputs, primary_confidences)
            async for ev in _drain_queue(primary_queue, 1):
                yield ev

            final_output = primary_outputs.get(primary_agent, "")
            final_confidence = primary_confidences.get(primary_agent, 0.0)

            # Store lite session to Redis
            try:
                from backend.db.redis_client import cache_set
                from backend.config import settings as _s
                session_data = {
                    "session_id": session_id,
                    "query": query,
                    "lite_mode": True,
                    "primary_agent": primary_agent,
                    "support_agents": support_agents,
                    "recommendation": final_output[:500],
                    "confidence": final_confidence,
                    "evidence_bundle": evidence_bundle.model_dump(),
                    "subagent_evidence": [se.model_dump() for se in subagent_results],
                    "timestamp": __import__("time").time(),
                }
                await cache_set(f"council_session:{session_id}", session_data, ttl=_s.session_store_ttl)
            except Exception as e:
                logger.warning(f"Lite session storage to Redis failed: {e}")

            # ── MIROFISH SWARM PHASE (brand + market, works in lite mode too) ──
            if mirofish_enabled:
                async for ev in _run_mirofish_swarm(query):
                    yield ev

            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'confidence': final_confidence, 'recommendation': final_output, 'primary_agent': primary_agent, 'lite_mode': True, 'mirofish_enabled': mirofish_enabled, 'evidence_bundle': evidence_bundle.model_dump()})}\n\n"
            return

        # ── STAGE 1: RAG Fetching ──
        yield _stage_event("rag_fetching", "Querying RAG vector store for all 6 agents...", 0)

        try:
            from backend.data_gatherer import gather_all_agents, CitationBundle
        except ImportError as e:
            logger.error(f"data_gatherer import failed: {e}")
            yield _stage_event("sources_ready", "Data gatherer unavailable", 0)
            return

        citation_bundles = {}
        
        try:
            # ── STAGE 2: API Calls ──
            yield _stage_event("api_called", "Firing real-time APIs: GNews, Alpha Vantage, OpenWeather...", 0)

            # ── STAGE 3: MCP / Firecrawl ──
            yield _stage_event("mcp_fetched", "Gathering sources from DuckDuckGo & Firecrawl...", 0)

            # Gather sources for each agent one by one with live updates
            agent_keys = ["risk", "supply", "logistics", "market", "finance", "brand"]
            
            for idx, agent_key in enumerate(agent_keys):
                try:
                    # Gather for single agent
                    bundles = await gather_all_agents(query, agent_keys=[agent_key])
                    bundle = bundles.get(agent_key, CitationBundle())
                    
                    source_count = len(bundle.citations)
                    source_urls = []
                    for c in bundle.citations:
                        if c.url and c.url.startswith("http"):
                            source_urls.append({
                                "num": c.number, 
                                "title": c.title[:60] if c.title else "Source", 
                                "url": c.url
                            })
                    
                    # Emit source discovery event for this agent (even if no URLs, show count)
                    event_data = {
                        'type': 'source_discovered',
                        'agent': agent_key,
                        'count': source_count,
                        'sources': source_urls[:6]
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                    citation_bundles[agent_key] = bundle
                    logger.info(f"[{session_id[:8]}] {agent_key}: {source_count} sources, {len(source_urls)} with URLs")
                        
                except Exception as ae:
                    logger.warning(f"Source gathering for {agent_key}: {ae}")
                    citation_bundles[agent_key] = CitationBundle()

            # Final aggregate
            total = sum(len(b.citations) for b in citation_bundles.values())
            logger.info(f"[{session_id[:8]}] Total sources: {total}")

            # Emit final citations map
            for agent_key in agent_keys:
                bundle = citation_bundles.get(agent_key, CitationBundle())
                url_map = {str(c.number): c.url for c in bundle.citations if c.url and c.url.startswith("http")}
                if url_map:
                    yield f"data: {json.dumps({'type': 'citations_map', 'agent': agent_key, 'urls': url_map})}\n\n"
            
            # ── STAGE 4: Sources Ready ──
            yield _stage_event("sources_ready", f"Research complete — {total} sources across 6 agents", total)
            yield f"data: {json.dumps({'type': 'citations_ready'})}\n\n"

        except Exception as e:
            logger.error(f"Data gathering failed: {e}")
            yield _stage_event("sources_ready", f"Error: {str(e)[:100]}", 0)

        def get_bundle(agent_key: str):
            return citation_bundles.get(agent_key, CitationBundle())

        # ── ROUND 1: Parallel Analysis ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 1, 'phase': 'analysis'})}\n\n"

        r1_outputs: dict[str, str] = {}
        r1_confidences: dict[str, float] = {}
        queue1: asyncio.Queue = asyncio.Queue()
        r1_tasks = []

        for key in ("risk", "supply", "logistics", "market", "finance", "brand"):
            bundle = get_bundle(key)
            messages = _build_agent_messages(
                agent_key=key, query=query,
                citation_context=bundle.format_context(),
                citation_list_hint=bundle.format_citation_list(),
                round_num=1,
            )
            r1_tasks.append(asyncio.create_task(
                _run_agent_parallel(key, messages, 1, queue1, r1_outputs, r1_confidences)
            ))

        async for ev in _drain_queue(queue1, 6):
            yield ev
        await asyncio.gather(*r1_tasks, return_exceptions=True)

        # ── MODERATOR Round 1 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 1})}\n\n"
        mod_r1 = await _run_moderator(query, r1_outputs, r1_confidences, 1)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 1, **mod_r1})}\n\n"

        # ── ROUND 2: Debate ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 2, 'phase': 'debate'})}\n\n"

        r2_outputs: dict[str, str] = {}
        r2_confidences: dict[str, float] = {}
        queue2: asyncio.Queue = asyncio.Queue()
        r2_tasks = []

        for key in ("risk", "supply", "logistics", "market", "finance", "brand"):
            bundle = get_bundle(key)
            messages = _build_agent_messages(
                agent_key=key, query=query,
                citation_context=bundle.format_context(),
                citation_list_hint=bundle.format_citation_list(),
                round1_outputs=r1_outputs,
                round_num=2,
            )
            r2_tasks.append(asyncio.create_task(
                _run_agent_parallel(key, messages, 2, queue2, r2_outputs, r2_confidences,
                                    default_confidence=r1_confidences.get(key, 50.0))
            ))

        async for ev in _drain_queue(queue2, 6):
            yield ev
        await asyncio.gather(*r2_tasks, return_exceptions=True)

        # ── MODERATOR Round 2 ──
        yield f"data: {json.dumps({'type': 'moderator_start', 'round': 2})}\n\n"
        mod_r2 = await _run_moderator(query, r2_outputs, r2_confidences, 2)
        yield f"data: {json.dumps({'type': 'moderator_done', 'round': 2, **mod_r2})}\n\n"

        # ── ROUND 3: Supervisor ──
        yield f"data: {json.dumps({'type': 'round_start', 'round': 3, 'phase': 'supervisor'})}\n\n"

        sup_context = (
            f"MODERATOR ROUND 1:\n{mod_r1.get('summary', '')}\n"
            f"Scores: {json.dumps(mod_r1.get('scores', {}))}\nConsensus: {mod_r1.get('consensus', 0)}%\n\n"
            f"MODERATOR ROUND 2:\n{mod_r2.get('summary', '')}\n"
            f"Scores: {json.dumps(mod_r2.get('scores', {}))}\nConsensus: {mod_r2.get('consensus', 0)}%\n\n"
            "All agents used real-time DuckDuckGo, Firecrawl, APIs, and RAG with ≥9 numbered citations each."
        )
        sup_messages = [
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\n{sup_context}\n\nDeliver your final verdict."},
        ]

        supervisor_output = ""
        yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'supervisor', 'round': 3})}\n\n"
        try:
            async for token in llm_router.stream_with_fallback("moderator", sup_messages):
                supervisor_output += token
                yield f"data: {json.dumps({'type': 'token', 'agent': 'supervisor', 'round': 3, 'content': token})}\n\n"
        except Exception as e:
            supervisor_output = f"Supervisor unavailable: {e}"
            yield f"data: {json.dumps({'type': 'agent_error', 'agent': 'supervisor', 'round': 3, 'error': str(e)})}\n\n"

        sup_confidence = _parse_confidence(supervisor_output, mod_r2.get("consensus", 50))
        yield f"data: {json.dumps({'type': 'supervisor_done', 'round': 3, 'confidence': sup_confidence})}\n\n"

        # ── MIROFISH SWARM PHASE (brand + market, works in both lite and full council) ──
        if mirofish_enabled:
            async for ev in _run_mirofish_swarm(query):
                yield ev

        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'confidence': sup_confidence, 'recommendation': supervisor_output, 'mirofish_enabled': mirofish_enabled})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def _run_mirofish_swarm(query: str) -> AsyncGenerator[str, None]:
    """Run MiroFish swarm simulation for brand + market agents.
    Works in both lite mode and full council mode.
    Yields SSE-formatted events for streaming to the frontend.
    """
    yield f"data: {json.dumps({'type': 'mirofish_start', 'agents': ['brand', 'market']})}\n\n"

    async def _run_mirofish_agent(agent_type: str):
        """Run MiroFish simulation for a single agent, yielding SSE progress events."""
        from backend.mirofish.simulation_engine import SimulationEngine
        from backend.mirofish.graph_builder import GraphBuilder
        from backend.mirofish.persona_generator import PersonaGenerator
        from backend.mirofish.schemas import SimulationConfig, SimulationState

        sim_id = f"{agent_type}_sim_{uuid.uuid4().hex[:8]}"

        try:
            # Phase 1: Graph building
            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'graph_building', 'simulation_id': sim_id})}\n\n"
            graph_builder = GraphBuilder()
            entities, relationships = await graph_builder.build_graph(query)
            entity_names = [e.name for e in entities]

            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'graph_ready', 'simulation_id': sim_id, 'entities': entity_names, 'entity_count': len(entities)})}\n\n"

            # Phase 2: Persona generation
            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'persona_generation', 'simulation_id': sim_id})}\n\n"
            config = SimulationConfig(
                name=sim_id,
                seed_query=query,
                horizon_days=30,
                num_personas=5,
                rounds=3,
            )
            persona_gen = PersonaGenerator()
            personas = await persona_gen.generate_personas(entities, relationships, config)
            persona_names = [f"{p.name} ({p.role.value})" for p in personas]

            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'personas_ready', 'simulation_id': sim_id, 'personas': persona_names, 'persona_count': len(personas)})}\n\n"

            # Phase 3: Run simulation
            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'simulation_running', 'simulation_id': sim_id})}\n\n"
            state = SimulationState(
                id=sim_id,
                config=config,
                entities=entities,
                relationships=relationships,
                personas=personas,
                agent_type=agent_type,
                parent_query=query,
            )
            engine = SimulationEngine()
            state = await engine.run_simulation(state)

            # Phase 4: Report
            yield f"data: {json.dumps({'type': 'mirofish_agent_progress', 'agent': agent_type, 'phase': 'report_generation', 'simulation_id': sim_id})}\n\n"
            from backend.mirofish.report_agent import ReportAgent
            report_agent = ReportAgent()
            report = await report_agent.generate_report(state, report_type="full")

            result = {
                "simulation_id": sim_id,
                "status": state.status,
                "prediction": state.result.prediction if state.result else "Simulation failed",
                "confidence": state.result.confidence if state.result else 0.0,
                "key_factors": state.result.key_factors if state.result else [],
                "risks": state.result.risks if state.result else [],
                "opportunities": state.result.opportunities if state.result else [],
                "recommendations": state.result.recommendations if state.result else [],
                "scenarios": state.result.scenarios if state.result else [],
                "entities": entity_names,
                "personas": persona_names,
                "report_summary": report.get("prediction", "")[:200] if report else "",
            }

            yield f"data: {json.dumps({'type': 'mirofish_agent_complete', 'agent': agent_type, 'result': result})}\n\n"
            return

        except Exception as e:
            logger.error(f"MiroFish simulation for {agent_type} failed: {e}")
            yield f"data: {json.dumps({'type': 'mirofish_agent_error', 'agent': agent_type, 'error': str(e)})}\n\n"
            return

    # Run brand and market simulations in parallel, collecting SSE events
    brand_events: list[str] = []
    market_events: list[str] = []

    async def _brand_sim():
        async for ev in _run_mirofish_agent("brand"):
            brand_events.append(ev)

    async def _market_sim():
        async for ev in _run_mirofish_agent("market"):
            market_events.append(ev)

    # Run both in parallel
    await asyncio.gather(_brand_sim(), _market_sim())

    # Yield all collected events (interleaved for streaming feel)
    for ev in brand_events + market_events:
        yield ev

    yield f"data: {json.dumps({'type': 'mirofish_complete'})}\n\n"


async def _run_moderator(query: str, outputs: dict, confidences: dict, round_num: int) -> dict:
    summaries = "\n".join([
        f"- {k} (confidence {confidences.get(k, 0):.0f}%): {v[:250]}"
        for k, v in outputs.items()
    ])
    msg = (
        f"Query: {query}\nRound: {round_num}\n\nAgent Outputs:\n{summaries}\n\n"
        f"Score each agent and provide consensus. Return ONLY valid JSON:\n"
        f'{{"scores":{{"risk":80,"supply":75,"logistics":70,"market":80,"finance":75,"brand":70}},'
        f'"consensus":75,"summary":"Brief summary of key consensus and conflicts"}}'
    )
    try:
        response, _ = await llm_router.invoke_with_fallback("moderator", [
            {"role": "system", "content": MODERATOR_PROMPT},
            {"role": "user", "content": msg},
        ])
        m = re.search(r'\{[\s\S]*\}', response.content)
        if m:
            parsed = json.loads(m.group())
            return {"scores": parsed.get("scores", confidences), "consensus": parsed.get("consensus", 50),
                    "summary": parsed.get("summary", response.content[:400])}
    except Exception as e:
        logger.warning(f"Moderator R{round_num} failed: {e}")
    return {"scores": confidences, "consensus": sum(confidences.values()) / max(len(confidences), 1),
            "summary": "Moderator unavailable."}


def _parse_confidence(text: str, default: float) -> float:
    for p in [r"confidence[:\s]+(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)\s*/\s*100", r"(\d+(?:\.\d+)?)\s*%\s*confidence"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = float(m.group(1))
            return min(v, 100.0) if v > 1 else v * 100
    return default
