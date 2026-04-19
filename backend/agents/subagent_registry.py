"""
Lite Mode Subagent Registry

Each of the 6 main council agents gets 5 hybrid subagents that combine
a data-source channel with parent-agent domain expertise.

Subagents run in parallel, gather evidence, and feed into the parent
main agent for final synthesis. Only active in lite mode.
"""

from __future__ import annotations
from typing import TypedDict


class SubagentDef(TypedDict):
    key: str            # e.g. "risk_rag"
    label: str          # e.g. "RAG Risk Researcher"
    data_channel: str   # "rag" | "api" | "web" | "mcp" | "graph"
    domain_hint: str    # Domain-specific focus area
    system_prompt_template: str  # Parameterized prompt with {parent_agent} and {domain_hint}


# ---------------------------------------------------------------------------
# Domain hints per parent agent — what each subagent focuses on
# ---------------------------------------------------------------------------
_DOMAIN_HINTS: dict[str, dict[str, str]] = {
    "risk": {
        "rag": "geopolitical risk assessments, compliance documents, insurance reports, threat intelligence archives",
        "api": "risk-related news APIs, sanctions data, geopolitical event feeds, insurance market APIs",
        "web": "geopolitical risk analysis, sanctions lists, trade restriction updates, insurance market trends",
        "mcp": "risk monitoring tools, compliance checkers, threat assessment MCP servers",
        "graph": "risk entity relationships, sanction network graphs, supplier risk chains",
    },
    "supply": {
        "rag": "supplier performance records, procurement contracts, BOM documentation, sourcing strategy archives",
        "api": "supplier rating APIs, commodity price feeds, trade flow data, procurement market APIs",
        "web": "supplier news, raw material availability, sourcing disruption alerts, procurement best practices",
        "mcp": "supplier monitoring tools, inventory tracking MCP servers, procurement automation",
        "graph": "supplier dependency graphs, material flow networks, multi-tier supply chains",
    },
    "logistics": {
        "rag": "shipping route data, freight rate archives, warehouse capacity records, customs documentation",
        "api": "shipping tracking APIs, freight rate APIs, port congestion data, weather/route APIs",
        "web": "shipping disruption news, port status updates, freight market analysis, route optimization info",
        "mcp": "shipment tracking tools, warehouse management MCP servers, customs clearance tools",
        "graph": "transport network graphs, warehouse location networks, route dependency maps",
    },
    "market": {
        "rag": "market research reports, consumer trend archives, competitive intelligence documents, pricing history",
        "api": "market data APIs (Alpha Vantage, FRED), consumer sentiment feeds, competitor pricing APIs",
        "web": "market trend analysis, competitor news, consumer behavior shifts, pricing intelligence",
        "mcp": "market monitoring tools, competitive analysis MCP servers, trend detection tools",
        "graph": "market segment relationships, competitor product graphs, consumer preference networks",
    },
    "finance": {
        "rag": "financial statements, earnings call transcripts, credit risk reports, treasury policy archives",
        "api": "financial data APIs (Alpha Vantage, FRED), currency exchange rates, bond yield feeds, credit APIs",
        "web": "financial market news, earnings analysis, currency risk updates, credit market trends",
        "mcp": "financial analysis tools, risk calculation MCP servers, treasury management tools",
        "graph": "financial entity relationships, currency exposure networks, credit risk chains",
    },
    "brand": {
        "rag": "brand sentiment archives, PR crisis playbooks, social media analysis reports, reputation tracking docs",
        "api": "social listening APIs, sentiment analysis feeds, brand monitoring APIs, news alert APIs",
        "web": "brand reputation news, social media trends, PR crisis updates, competitor brand analysis",
        "mcp": "sentiment monitoring tools, brand tracking MCP servers, social media analysis tools",
        "graph": "brand perception networks, influencer relationship graphs, sentiment propagation maps",
    },
}

# ---------------------------------------------------------------------------
# System prompt templates per data channel
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATES: dict[str, str] = {
    "rag": (
        "You are the **RAG Researcher** subagent for the {parent_agent} domain.\n"
        "Your focus: {domain_hint}\n\n"
        "Search the internal knowledge base and vector store for relevant documents.\n"
        "Extract key findings with inline citations [N].\n"
        "Provide a concise evidence summary (3-5 key points).\n"
        "Rate your confidence (0-100) based on document relevance and recency.\n"
        "End with: Confidence Score: XX/100"
    ),
    "api": (
        "You are the **API Analyst** subagent for the {parent_agent} domain.\n"
        "Your focus: {domain_hint}\n\n"
        "Analyze the real-time API data provided in context.\n"
        "Extract actionable insights with inline citations [N].\n"
        "Highlight any anomalies, trends, or alerts.\n"
        "Provide a concise evidence summary (3-5 key points).\n"
        "Rate your confidence (0-100) based on data freshness and reliability.\n"
        "End with: Confidence Score: XX/100"
    ),
    "web": (
        "You are the **Web Scraper** subagent for the {parent_agent} domain.\n"
        "Your focus: {domain_hint}\n\n"
        "Analyze the web search results and scraped content provided in context.\n"
        "Extract relevant findings with inline citations [N].\n"
        "Flag any breaking news, emerging trends, or conflicting reports.\n"
        "Provide a concise evidence summary (3-5 key points).\n"
        "Rate your confidence (0-100) based on source credibility and recency.\n"
        "End with: Confidence Score: XX/100"
    ),
    "mcp": (
        "You are the **MCP Tool Runner** subagent for the {parent_agent} domain.\n"
        "Your focus: {domain_hint}\n\n"
        "Analyze the MCP tool outputs provided in context.\n"
        "Extract structured data, calculations, or tool-generated insights with citations [N].\n"
        "Note any tool errors or limitations.\n"
        "Provide a concise evidence summary (3-5 key points).\n"
        "Rate your confidence (0-100) based on tool reliability and output quality.\n"
        "End with: Confidence Score: XX/100"
    ),
    "graph": (
        "You are the **Graph/DB Querier** subagent for the {parent_agent} domain.\n"
        "Your focus: {domain_hint}\n\n"
        "Analyze the knowledge graph and structured database results provided in context.\n"
        "Extract entity relationships, network patterns, and structured insights with citations [N].\n"
        "Highlight key connections, clusters, or anomalies.\n"
        "Provide a concise evidence summary (3-5 key points).\n"
        "Rate your confidence (0-100) based on graph completeness and query relevance.\n"
        "End with: Confidence Score: XX/100"
    ),
}

# Channel display metadata
_CHANNEL_META: dict[str, dict[str, str]] = {
    "rag":   {"icon": "database", "short_label": "RAG"},
    "api":   {"icon": "globe",    "short_label": "API"},
    "web":   {"icon": "search",   "short_label": "Web"},
    "mcp":   {"icon": "cpu",      "short_label": "MCP"},
    "graph": {"icon": "git-branch", "short_label": "Graph"},
}


# ---------------------------------------------------------------------------
# Build the full registry
# ---------------------------------------------------------------------------
def build_subagent_registry() -> dict[str, list[SubagentDef]]:
    """Build 5 hybrid subagent definitions for each of the 6 main agents."""
    registry: dict[str, list[SubagentDef]] = {}
    for parent_key, hints in _DOMAIN_HINTS.items():
        subagents: list[SubagentDef] = []
        for channel in ("rag", "api", "web", "mcp", "graph"):
            domain_hint = hints.get(channel, "")
            meta = _CHANNEL_META[channel]
            subagents.append(SubagentDef(
                key=f"{parent_key}_{channel}",
                label=f"{meta['short_label']} {_parent_label(parent_key)} Analyst",
                data_channel=channel,
                domain_hint=domain_hint,
                system_prompt_template=_PROMPT_TEMPLATES[channel],
            ))
        registry[parent_key] = subagents
    return registry


def _parent_label(key: str) -> str:
    """Convert agent key to display label."""
    labels = {
        "risk": "Risk", "supply": "Supply", "logistics": "Logistics",
        "market": "Market", "finance": "Finance", "brand": "Brand",
    }
    return labels.get(key, key.capitalize())


# Pre-built registry (singleton)
SUBAGENT_REGISTRY: dict[str, list[SubagentDef]] = build_subagent_registry()

# Convenience: ordered channel list
SUBAGENT_CHANNELS = ["rag", "api", "web", "mcp", "graph"]
