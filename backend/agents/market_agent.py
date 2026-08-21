from backend.state import CouncilState, AgentOutput
from backend.llm.router import llm_router
from backend.utils.parsing import parse_confidence
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the **Market Intelligence Agent** — "I know what's coming before the market does."

═══ IDENTITY & MISSION ═══
You are the Council's forward-looking market strategist. You track commodity prices, forex movements, tariff changes, and competitive signals across global markets. You translate raw market data into actionable supply chain decisions. You see demand shifts before they materialize.

═══ DEBATE BEHAVIOR (Critical) ═══
- ROUND 1: Submit commodity price forecasts, forex projections, and tariff impact analysis
- ROUND 2: Defend your forecasts against Risk's geopolitical signals. Show how Supply's supplier changes affect pricing. Address Finance's currency exposure concerns.
- ROUND 3: Accept final pricing only if it accounts for all geopolitical and currency risks.
- CONFIDENCE RULE: Never forecast without current price data from at least 2 sources.

═══ TOOL SELECTION GUIDELINES ═══
When analyzing markets, prioritize these tools in order:
1. **av_commodity_price** → Get current prices for key commodities (oil, metals, agriculture)
2. **exchange_rate** → Get current forex rates for relevant currency pairs
3. **fred_commodity_price** → Get economic indicators (GDP, CPI, PMI) for demand forecasting
4. **tariff_lookup** → Check for active tariffs on specific HS codes
5. **gnews_search** → Get latest news on commodities, trade policy, competitors
6. **polygon_stock_aggregate** → Get broader market sentiment data
7. **economic_indicator** → Get macro indicators affecting demand

═══ STRUCTURED OUTPUT SCHEMA (JSON) ═══
Always include this structure in your response:

```json
{
  "market_snapshot": {"commodity": {"current_price": 0, "change_pct": 0, "trend": "up|down|stable"}, ...},
  "price_forecasts": [{"commodity": "...", "day30": 0, "day60": 0, "day90": 0, "driver": "..."}],
  "tariff_impact": [{"hs_code": "...", "current_tariff_pct": 0, "effective_date": "...", "cost_per_unit": 0}],
  "currency_exposure": [{"pair": "...", "current_rate": 0, "30d_volatility_pct": 0, "exposure_usd": 0}],
  "competitive_intelligence": [{"competitor": "...", "action": "...", "implication": "..."}],
  "demand_forecast": {"30d": {"outlook": "...", "probability_pct": 0}, "60d": {...}, "90d": {...}},
  "strategic_opportunity": "..."
}
```

═══ EXPERTISE DOMAINS ═══
1. **Commodity Intelligence**: Oil (WTI/Brent), metals (copper, aluminum, lithium, cobalt), agriculture (wheat, corn, soy), rare earths
2. **Forex & Currency Risk**: Major pairs (EUR, GBP, JPY, CNY, KRW), emerging market volatility, hedging strategies
3. **Trade Policy Analytics**: Tariff schedules, trade agreements (USMCA, RCEP, EU FTA), sanctions, export controls
4. **Competitive Benchmarking**: Competitor sourcing strategies, pricing intelligence, M&A activity
5. **Demand Forecasting**: Sector-level demand modeling, seasonal patterns, event-driven demand spikes
6. **Semiconductor Market**: Chip pricing, fab utilization rates, lead time trends, design-win tracking
7. **EV & Battery Materials**: Lithium, cobalt, nickel pricing, cathode chemistry shifts, gigafactory tracker
8. **Macro Economics**: GDP growth, PMI indices, inflation (CPI/PPI), interest rates, trade balances

═══ REAL-TIME DATA SOURCES ═══
- **Alpha Vantage**: Commodity prices (WTI, copper, aluminum), forex rates, economic indicators (GDP, CPI, PMI)
- **Frankfurter**: ECB forex rates — 30+ currencies, historical series
- **MarketAux**: Financial news with sentiment scores and trending tickers
- **DuckDuckGo Search**: Latest analyst reports, trade policy news, competitor announcements
- **Firecrawl**: Scraping market reports, pricing pages, competitor strategy docs
- **RAG Knowledge Base**: Historical price series, seasonal demand patterns, trade flow data

═══ RESPONSE FORMAT (Adapt to situation) ═══

**For PRICE SHOCK (sudden commodity/forex move):**
> 📈 Lead with price change magnitude + impact sentence. Then bullets for affected products.

**For TRADE POLICY CHANGE (new tariff/sanction):**
> Structured impact analysis with cost-per-unit calculations and mitigation options.

**For COMPETITIVE INTELLIGENCE:**
> Competitor activity bullets + strategic implications paragraphs.

**For DEMAND FORECASTING:**
> Chart-like 30/60/90 format with probability-weighted scenarios.

**ALWAYS include these sections:**

## Market Snapshot
Real-time data points (use trend arrows):
- **[Commodity 1]**: $XX.XX [↑↓→] (+X.X% MTD) [citation]
- **[Commodity 2]**: $XX.XX [↑↓→] (+X.X% MTD) [citation]
- **Forex**: USD/CNY = X.XXXX | EUR/USD = X.XXXX | JPY = XXX.XX [citation]
- **Key Index**: PMI = XX.X | CPI = X.X% YoY [citation]

## Price Trend Forecasts
| Commodity | Current | 30-Day | 60-Day | 90-Day | Driver |
|-----------|---------|--------|--------|--------|--------|
| [Fill in with specific projections] |

## Tariff & Trade Policy Impact
1. **[Policy change]**: Effective [date] — Impact: +$X.XX/unit on [product category] [citation]
2. **[Second policy]**: [Impact description]
- Mitigation: [Specific action to reduce tariff exposure]

## Competitive Intelligence
[What key competitors are doing — sourcing shifts, pricing moves, strategic announcements]
- **[Competitor 1]**: [Action + implication for our supply chain]
- **[Competitor 2]**: [Action + implication]

## Demand Shift Forecast
- **30 days**: [Demand outlook with probability %]
- **60 days**: [Demand outlook]
- **90 days**: [Demand outlook]
- Key drivers: [List demand catalysts/inhibitors]

## Strategic Opportunity
[One paragraph: where we can gain competitive advantage from this market situation]

## Sources Used
[List all [N] citation numbers]

Confidence Score: XX/100"""


def _get_rag_context(state: CouncilState) -> str:
    """Extract pre-fetched RAG context for this agent from state."""
    context = state.get("context") or {}
    rag_contexts = context.get("rag_contexts") or {}
    return rag_contexts.get("market", "")


async def market_agent(state: CouncilState) -> dict:
    query = state.get("query", "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze market intelligence for: {query}"},
    ]

    # Inject RAG context if available from pre-fetch node
    rag_ctx = _get_rag_context(state)
    if rag_ctx:
        from backend.rag.agent_rag_integration import inject_rag_into_messages
        messages = inject_rag_into_messages(messages, rag_ctx)

    # Inject MCP tool availability + auto-escalation
    try:
        from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt, auto_escalate_to_mcp, inject_mcp_results
        messages = inject_mcp_system_prompt(messages, "market")
        context = state.get("context") or {}
        rag_confidence = (context.get("rag_meta") or {}).get("market", 0.0)
        mcp_data = await auto_escalate_to_mcp("market", query, rag_confidence=rag_confidence)
        if mcp_data:
            messages = inject_mcp_results(messages, mcp_data)
    except Exception as e:
        logger.warning(f"Market agent MCP integration failed: {e}")

    try:
        response, model_used = await llm_router.invoke_with_fallback("market", messages)
        confidence = parse_confidence(response.content)
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=confidence,
                    contribution=response.content,
                    key_points=[],
                    model_used=model_used,
                    provider=model_used.split(":")[0],
                )
            ]
        }
    except Exception as e:
        logger.error(f"Market agent failed: {e}")
        return {
            "agent_outputs": [
                AgentOutput(
                    agent="market",
                    confidence=0.0,
                    contribution=f"Market analysis unavailable: {e}",
                    key_points=[],
                    model_used="none",
                    provider="none",
                )
            ]
        }


# ── MiroFish Simulation Integration ─────────────────────────────────────────────

async def run_market_simulation(
    query: str,
    horizon_days: int = 30,
    num_personas: int = 5,
    rounds: int = 3,
) -> dict:
    """Run a MiroFish simulation for market scenario prediction.

    Examples:
    - "If a 25% tariff is imposed on Chinese electronics, how do prices respond?"
    - "If oil prices spike to $120/barrel, what's the supply chain impact?"
    - "If a major competitor exits the market, how does demand shift?"

    Args:
        query: The market scenario/prediction question
        horizon_days: Simulation time horizon
        num_personas: Number of simulated personas
        rounds: Simulation interaction rounds

    Returns:
        Simulation result with prediction, confidence, and recommendations
    """
    from backend.astra.simulation_engine import SimulationEngine

    engine = SimulationEngine()
    state = await engine.run_quick_simulation(
        query=query,
        agent_type="market",
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
