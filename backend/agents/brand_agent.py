"""Brand Protector Agent for SupplyChainGPT Council.

Enhanced with:
  - Confidence parsing from LLM response
  - Real-time sentiment analysis via MCP news/social tools
  - Auto-generated crisis communication drafts
  - Advertising pivot recommendations
  - Competitor counter-messaging strategies
"""

import re
import json
import logging
from typing import Optional

from backend.state import CouncilState, AgentOutput, BrandSentiment
from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the **Brand Protector Agent** — "I protect the brand when supply chains break."

═══ IDENTITY & MISSION ═══
You are the Council's chief communications strategist and brand guardian. When supply chains fail, you control the narrative. You monitor sentiment, draft crisis communications, pivot advertising, and detect competitor exploitation — all in real-time. Your goal: protect brand equity and customer trust.

═══ DEBATE BEHAVIOR (Critical) ═══
- ROUND 1: Submit brand sentiment score, crisis level, and immediate containment actions
- ROUND 2: DEFEND brand against any agent underplaying the reputational risk. Challenge Supply's timeline if customer notification needed. Challenge Risk if they're causing panic.
- ROUND 3: Accept final comms only if you've approved all customer-facing messages.
- CONFIDENCE RULE: Never assess brand impact without checking current news sentiment.

═══ TOOL SELECTION GUIDELINES ═══
When protecting brand, prioritize these tools in order:
1. **gnews_search** → Get real-time news mentions with sentiment
2. **currents_brand_sentiment** → Get social media sentiment analysis
3. **gdelt_tone** → Get media tone analysis (positive/negative intensity)
4. **competitor_ads** → Monitor competitor advertising during crisis
5. **web_scrape_news** → Deep scrape specific news articles
6. **mediastack_news_search** → Get breaking news on the crisis

═══ STRUCTURED OUTPUT SCHEMA (JSON) ═══
Always include this structure in your response:

```json
{
  "brand_status": "STABLE|AT_RISK|CRISIS",
  "sentiment_score": -1.0 to 1.0,
  "sentiment_trend": "improving|stable|deteriorating",
  "news_mentions_24h": 0,
  "media_tone": {"positive_pct": 0, "neutral_pct": 0, "negative_pct": 0},
  "crisis_level": "LOW|MEDIUM|HIGH|SEVERE",
  "immediate_actions": [{"action": "...", "timeline": "1h|4h|24h", "owner": "..."}],
  "communication_drafts": {"customer_email": "...", "social_post": "...", "press_statement": "..."},
  "advertising_response": {"pause": ["list"], "modify": ["list"], "launch": ["list"]},
  "competitor_monitoring": [{"competitor": "...", "action": "...", "response": "..."}],
  "customer_retention": [{"action": "...", "target": "...", "impact": "..."}],
  "recovery_timeline": {"day1": "...", "day7": "...", "day30": "..."}
}
```

═══ EXPERTISE DOMAINS ═══
1. **Crisis Communication**: Press releases, customer notifications, social media responses, internal memos
2. **Sentiment Monitoring**: Real-time brand mention tracking, tone analysis, volume spikes, virality detection
3. **Advertising Pivot**: Campaign pause/launch decisions, messaging shifts, channel reallocation
4. **Competitor Exploitation Detection**: Identifying when competitors use our disruption against us
5. **Customer Retention**: Proactive outreach, loyalty program activation, compensation strategies
6. **Stakeholder Management**: Investor communications, board briefings, regulatory notifications
7. **Social Media Crisis Management**: Platform-specific response strategies (X/Twitter, LinkedIn, Reddit)
8. **Reputation Recovery**: Post-crisis brand rebuilding playbook, trust metrics, NPS recovery

═══ REAL-TIME DATA SOURCES ═══
- **GNews**: Real-time news mentions — sentiment, volume, trending topics
- **GDELT**: Global media tone analysis — positive/negative coverage intensity
- **MarketAux**: Financial news impact on brand/sector perception
- **DuckDuckGo Search**: Latest brand mentions, competitor activity, social trends
- **Firecrawl**: Scraping competitor PR pages, customer review sites, social media feeds
- **RAG Knowledge Base**: Past crisis playbooks, customer communication templates, brand guidelines

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For ACTIVE CRISIS (brand under attack now):**
> 🚨 CRISIS STATUS in bold → immediate containment actions → ready-to-send communication drafts.

**For EMERGING THREAT (negative trend developing):**
> Sentiment trend analysis with data → proactive communication recommendations.

**For ROUTINE MONITORING (steady state):**
> Brand health dashboard with metrics → competitive positioning analysis.

**ALWAYS include these sections:**

## Brand Sentiment Dashboard
**Status: [🟢 STABLE / 🟡 AT RISK / 🔴 CRISIS]** | Sentiment Score: X/10 | Trend: [↑↓→]
- News mentions (24h): XXX (vs. avg: XX) [citation]
- Media tone: [Positive X% / Neutral X% / Negative X%] [citation]
- Social volume: [Normal / Elevated / Viral]
- Key platforms: [Where the conversation is happening]

## Immediate Crisis Response (if needed)
1. **[First action — within 1 hour]**: [Specific step with responsible team]
2. **[Second action — within 4 hours]**: [Specific step]
3. **[Third action — within 24 hours]**: [Specific step]

## Communication Drafts (Ready to Deploy)

**Customer Email (2-3 sentences):**
> "[Draft — empathetic, transparent, actionable]"

**Social Media Post (tweet-length):**
> "[Draft — concise, human, solution-focused]"

**Press Statement (one paragraph):**
> "[Draft — professional, factual, forward-looking]"

**Internal Memo (for leadership):**
> "[Draft — candid situation assessment with action items]"

## Advertising Response
- **PAUSE immediately**: [List campaigns to halt with reason]
- **MODIFY messaging**: [Campaigns to adjust — new angle/tone]
- **LAUNCH**: [New messaging opportunity — capitalize on situation]
- **Channel shift**: [Budget reallocation recommendation]

## Competitor Activity Monitor
⚠️ **[Competitor 1]**: [What they're doing — e.g., "Launching 'reliable supply' campaign targeting our customers"]
⚠️ **[Competitor 2]**: [Activity + response recommendation]

## Customer Retention Actions
1. [Proactive outreach step with target audience]
2. [Loyalty/compensation offer if needed]
3. [Long-term trust rebuilding measure]

## Brand Recovery Timeline
- **24 hours**: [Containment milestone]
- **1 week**: [Stabilization milestone]
- **30 days**: [Recovery milestone — target sentiment score]

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("brand", "")


def _parse_confidence(text: str, default: float = 50.0) -> float:
    """Extract confidence score from LLM response text."""
    patterns = [
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        r"confidence\s+score[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*%\s*confidence",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return min(val, 100.0) if val > 1 else val * 100
    return default


def _parse_sentiment(text: str) -> str:
    """Detect overall sentiment category from LLM response."""
    lower = text.lower()
    if any(kw in lower for kw in ["crisis", "severe", "critical", "emergency"]):
        return "crisis"
    if any(kw in lower for kw in ["negative", "concern", "risk", "damage", "threat"]):
        return "negative"
    if any(kw in lower for kw in ["positive", "opportunity", "strong", "favorable"]):
        return "positive"
    return "neutral"


def _extract_key_points(text: str, max_points: int = 5) -> list[str]:
    """Extract key points from structured LLM response."""
    points = []
    for line in text.split("\n"):
        line = line.strip()
        if re.match(r"^[\d]+[\.\)]\s", line) or line.startswith("- ") or line.startswith("• "):
            clean = re.sub(r"^[\d]+[\.\)]\s*", "", line)
            clean = re.sub(r"^[-•]\s*", "", clean)
            if clean and len(clean) > 10:
                points.append(clean[:200])
            if len(points) >= max_points:
                break
    return points


async def _fetch_brand_mcp_data(query: str) -> str:
    """Fetch news and social data from MCP tools for brand analysis."""
    results = []
    try:
        from backend.mcp.secure_mcp import secure_invoke
        news_result = await secure_invoke("brand", "news_search", {"query": query})
        if news_result.get("success"):
            results.append(f"NEWS: {json.dumps(news_result['result'], default=str)[:1000]}")
        reddit_result = await secure_invoke("brand", "reddit_search", {"query": query})
        if reddit_result.get("success"):
            results.append(f"SOCIAL: {json.dumps(reddit_result['result'], default=str)[:1000]}")
    except Exception as e:
        logger.warning(f"MCP data fetch for brand failed: {e}")
        results.append(f"MCP data unavailable: {e}")
    return "\n\n".join(results) if results else ""


async def _generate_crisis_comm(query: str, brand_analysis: str, confidence: float) -> Optional[str]:
    """Auto-generate a crisis communication draft."""
    prompt = f"""You are a Crisis Communications Director. Draft a professional crisis communication based on the brand analysis.

Crisis Context: {query}
Brand Analysis: {brand_analysis[:1500]}
Confidence: {confidence}%

Draft a press release that:
1. Acknowledges the situation transparently
2. Shows empathy and concern for stakeholders
3. Outlines immediate actions being taken
4. Provides timeline for updates
5. Includes contact information for media inquiries

Format as a press release suitable for immediate distribution."""

    try:
        response, _ = await llm_router.invoke_with_fallback("brand", [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Draft crisis communication for: {query}"},
        ])
        return response.content[:2000]
    except Exception as e:
        logger.error(f"Crisis comm generation failed: {e}")
        return None


async def _generate_ad_pivot(query: str, brand_analysis: str) -> Optional[str]:
    """Recommend advertising pivot based on brand sentiment."""
    prompt = f"""You are an Advertising Strategy Consultant. Based on the current brand sentiment, recommend advertising pivots.

Crisis Context: {query}
Brand Analysis: {brand_analysis[:1500]}

Recommend:
1. Which campaigns to pause immediately
2. New messaging angles that address the crisis
3. Channel shifts (e.g., from awareness to reassurance)
4. Budget reallocation recommendations
5. Timeline for resuming normal advertising

Format as actionable recommendations with specific next steps."""

    try:
        response, _ = await llm_router.invoke_with_fallback("brand", [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Recommend ad pivot for: {query}"},
        ])
        return response.content[:2000]
    except Exception as e:
        logger.error(f"Ad pivot recommendation failed: {e}")
        return None


async def brand_agent(state: CouncilState) -> dict:
    """Brand Protector Agent with sentiment analysis, crisis comms, and ad pivots.

    Runs the core brand assessment, then enhances with:
    - MCP-fetched news/social data for real-time sentiment
    - Crisis communication draft if sentiment is negative/crisis
    - Ad pivot recommendations if sentiment score < -0.3
    """
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Assess brand impact and crisis response for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "brand")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("brand", 0.0)
        mcp_data = await auto_escalate_to_mcp("brand", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Brand agent MCP integration failed: {e}")

    # Fetch real-time brand data from MCP
    mcp_brand_data = ""
    try:
        mcp_brand_data = await _fetch_brand_mcp_data(query)
        if mcp_brand_data:
            messages.append({"role": "user", "content": f"Real-time brand data:\n{mcp_brand_data[:2000]}"})
    except Exception as e:
        logger.warning(f"Brand MCP data fetch failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("brand", messages)
        content = response.content
        confidence = _parse_confidence(content)
        sentiment = _parse_sentiment(content)
        key_points = _extract_key_points(content)

        # Generate crisis communication if negative/crisis sentiment
        crisis_comm = None
        ad_pivot = None
        if sentiment in ("negative", "crisis"):
            crisis_comm = await _generate_crisis_comm(query, content, confidence)
        if sentiment in ("negative", "crisis") and confidence < 50:
            ad_pivot = await _generate_ad_pivot(query, content)

        # Build brand sentiment data for state
        brand_sentiment = BrandSentiment(
            overall_sentiment=sentiment,
            sentiment_score=-0.5 if sentiment == "crisis" else (-0.2 if sentiment == "negative" else (0.3 if sentiment == "positive" else 0.0)),
            trending_topics=[p[:80] for p in key_points[:3]],
            crisis_keywords=[kw for kw in ["crisis", "emergency", "recall", "scandal", "boycott"] if kw in content.lower()],
            recommended_actions=key_points[:3],
            crisis_comm_draft=crisis_comm,
            ad_pivot_recommendation=ad_pivot,
        )

        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=confidence,
                    contribution=content,
                    key_points=key_points,
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ],
            "brand_sentiment": brand_sentiment.model_dump(),
        }
    except Exception as e:
        logger.error(f"Brand agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="brand",
                    confidence=0.0,
                    contribution=f"Brand analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }


# ── MiroFish Simulation Integration ─────────────────────────────────────────────

async def run_brand_simulation(
    query: str,
    horizon_days: int = 30,
    num_personas: int = 5,
    rounds: int = 3,
) -> dict:
    """Run a MiroFish simulation for brand scenario prediction.

    Examples:
    - "If a competitor launches a negative campaign, how does sentiment evolve?"
    - "If we recall a product, how does media coverage spread?"
    - "If a spokesperson makes a controversial statement, what's the fallout?"

    Args:
        query: The brand scenario/prediction question
        horizon_days: Simulation time horizon
        num_personas: Number of simulated personas
        rounds: Simulation interaction rounds

    Returns:
        Simulation result with prediction, confidence, and recommendations
    """
    from backend.mirofish.simulation_engine import SimulationEngine

    engine = SimulationEngine()
    state = await engine.run_quick_simulation(
        query=query,
        agent_type="brand",
        horizon_days=horizon_days,
        num_personas=num_personas,
        rounds=rounds,
    )

    return {
        "simulation_id": state.id,
        "status": state.status,
        "prediction": state.result.prediction if state.result else "Simulation failed",
        "confidence": state.result.confidence if state.result else 0.0,
        "key_factors": state.result.key_factors if state.result else [],
        "risks": state.result.risks if state.result else [],
        "opportunities": state.result.opportunities if state.result else [],
        "recommendations": state.result.recommendations if state.result else [],
        "scenarios": state.result.scenarios if state.result else [],
        "personas": [f"{p.name} ({p.role.value})" for p in state.personas],
        "entities": [e.name for e in state.entities],
    }
