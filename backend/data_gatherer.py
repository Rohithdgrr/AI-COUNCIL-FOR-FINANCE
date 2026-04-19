"""Real-time data gathering for Council agents.

Sources used (in order, until ≥9 citations gathered):
  1-3. DuckDuckGo web search (top results with snippets)
  4-5. Firecrawl page scrape (top DDG URLs → markdown text)
  6-7. Real APIs: GNews / MarketAux / Alpha Vantage / OpenWeather / NOAA (based on agent domain)
  8.   RAG vector store (internal knowledge base)
  9+.  Additional APIs: GDELT, Frankfurter forex, GraphHopper, Shodan, NVD CVE

Returns a CitationBundle with numbered citations and formatted context string.
"""

import asyncio
import logging
import os
import httpx
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Source configs per agent ──────────────────────────────────────────────────
AGENT_SEARCH_QUERIES = {
    "risk":      ["supply chain geopolitical risk {query}", "supplier disruption news {query}", "cyber threat supply chain {query}"],
    "supply":    ["supplier shortage {query}", "alternative supplier {query}", "procurement supply chain {query}"],
    "logistics": ["shipping route disruption {query}", "port congestion freight {query}", "logistics delay {query}"],
    "market":    ["commodity price forecast {query}", "trade tariff impact {query}", "market trend {query}"],
    "finance":   ["financial impact supply chain {query}", "forex exchange rate {query}", "economic indicator {query}"],
    "brand":     ["brand reputation crisis {query}", "consumer sentiment supply chain {query}", "PR crisis {query}"],
    "moderator": ["supply chain analysis {query}", "expert opinion {query}", "industry report {query}"],
}

AGENT_API_SOURCES = {
    "risk":      ["gnews", "gdelt", "nvd", "openweather", "noaa"],
    "supply":    ["gnews", "marketaux", "alpha_vantage", "frankfurter"],
    "logistics": ["gnews", "openweather", "noaa", "graphhopper"],
    "market":    ["marketaux", "alpha_vantage", "gnews", "frankfurter"],
    "finance":   ["alpha_vantage", "frankfurter", "marketaux", "gnews"],
    "brand":     ["gnews", "marketaux", "gdelt"],
    "moderator": ["gnews", "marketaux", "alpha_vantage"],
}


@dataclass
class Citation:
    number: int
    source: str          # "DuckDuckGo", "Firecrawl", "GNews", "RAG", etc.
    title: str
    url: str
    snippet: str         # The actual content chunk


@dataclass
class CitationBundle:
    citations: list[Citation] = field(default_factory=list)

    def format_context(self) -> str:
        """Format all citations as a numbered context block for LLM injection."""
        if not self.citations:
            return ""
        lines = ["## Real-Time Research Context\n"]
        for c in self.citations:
            lines.append(f"[{c.number}] **{c.source}** — {c.title}")
            lines.append(f"    URL: {c.url}")
            lines.append(f"    {c.snippet[:400]}")
            lines.append("")
        return "\n".join(lines)

    def format_citation_list(self) -> str:
        """Format citations section for end of agent response."""
        if not self.citations:
            return ""
        lines = ["\n\n---\n## Sources & Citations\n"]
        for c in self.citations:
            lines.append(f"[{c.number}] {c.title} — *{c.source}*")
            if c.url and c.url.startswith("http"):
                lines.append(f"    {c.url}")
        return "\n".join(lines)


# ── DuckDuckGo search ─────────────────────────────────────────────────────────
async def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo and return list of {title, url, body} results."""
    try:
        try:
            from ddgs import DDGS  # new package name
        except ImportError:
            from duckduckgo_search import DDGS  # fallback to old name
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:500],
                })
        logger.info(f"DDG search '{query[:50]}' → {len(results)} results")
        return results
    except Exception as e:
        logger.warning(f"DDG search failed for '{query[:50]}': {e}")
        return []



# ── Firecrawl scrape ──────────────────────────────────────────────────────────
async def _firecrawl_scrape(url: str) -> Optional[str]:
    """Scrape a URL using Firecrawl (self-hosted or cloud). Returns markdown text."""
    base_url = os.getenv("FIRECRAWL_BASE_URL", "").rstrip("/")
    api_key = os.getenv("FIRECRAWL_API_KEY", "")

    # Firecrawl not configured — try lightweight requests fallback
    if not base_url:
        return await _requests_scrape(url)

    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(
                f"{base_url}/v1/scrape",
                json={"url": url, "formats": ["markdown"]},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("data", {}).get("markdown", "") or data.get("markdown", "")
                if content:
                    logger.info(f"Firecrawl scraped {url} → {len(content)} chars")
                    return content[:1500]
    except Exception as e:
        logger.warning(f"Firecrawl scrape failed for {url}: {e}")

    return await _requests_scrape(url)


async def _requests_scrape(url: str) -> Optional[str]:
    """Lightweight HTML→text fallback scraper."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 SupplyChainGPT/1.0"})
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                # Strip HTML tags crudely — good enough for snippet extraction
                import re
                text = re.sub(r'<[^>]+>', ' ', resp.text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:1500]
    except Exception as e:
        logger.debug(f"Requests scrape failed for {url}: {e}")
    return None


# ── Real API fetchers ──────────────────────────────────────────────────────────
async def _fetch_gnews(query: str) -> list[dict]:
    """GNews API — latest news articles."""
    api_key = os.getenv("GNEWS_API_KEY", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://gnews.io/api/v4/search",
                params={"q": query[:100], "token": api_key, "max": 5, "lang": "en"},
            )
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                return [{"title": a.get("title", ""), "url": a.get("url", ""), "snippet": a.get("description", "") or a.get("content", "")[:300]} for a in articles]
    except Exception as e:
        logger.debug(f"GNews failed: {e}")
    return []


async def _fetch_marketaux(query: str) -> list[dict]:
    """MarketAux — financial news with sentiment."""
    api_key = os.getenv("MARKETAUX_API_KEY", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.marketaux.com/v1/news/all",
                params={"search": query[:100], "api_token": api_key, "limit": 3},
            )
            if resp.status_code == 200:
                articles = resp.json().get("data", [])
                return [{"title": a.get("title", ""), "url": a.get("url", ""), "snippet": a.get("description", "") or a.get("snippet", "")[:300]} for a in articles]
    except Exception as e:
        logger.debug(f"MarketAux failed: {e}")
    return []


async def _fetch_alpha_vantage(query: str) -> list[dict]:
    """Alpha Vantage — commodity & stock market data."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        return []
    try:
        # News sentiment endpoint
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.alphavantage.co/query",
                params={"function": "NEWS_SENTIMENT", "tickers": "SPY", "topics": "economy_macro", "apikey": api_key, "limit": 3},
            )
            if resp.status_code == 200:
                feed = resp.json().get("feed", [])
                return [{"title": a.get("title", ""), "url": a.get("url", ""), "snippet": a.get("summary", "")[:300]} for a in feed[:3]]
    except Exception as e:
        logger.debug(f"Alpha Vantage failed: {e}")
    return []


async def _fetch_openweather(query: str) -> list[dict]:
    """OpenWeatherMap — weather alerts for logistics disruptions."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        return []
    try:
        # Extract location from query or use default major port cities
        import re
        location_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', query)
        location = location_match.group(1) if location_match else "Shanghai"
        
        # Common supply chain cities
        supply_chain_cities = ["Shanghai", "Singapore", "Rotterdam", "Los Angeles", "Hong Kong"]
        if location not in supply_chain_cities and any(city.lower() in query.lower() for city in supply_chain_cities):
            location = next(city for city in supply_chain_cities if city.lower() in query.lower())
        
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": location, "appid": api_key, "units": "metric"},
            )
            if resp.status_code == 200:
                d = resp.json()
                desc = d.get("weather", [{}])[0].get("description", "")
                temp = d.get("main", {}).get("temp", "N/A")
                wind = d.get("wind", {}).get("speed", "N/A")
                return [{"title": f"{location} Weather (Supply Chain Hub)", "url": "https://openweathermap.org", "snippet": f"Current conditions: {desc}, Temp: {temp}°C, Wind: {wind} m/s. Affects {location} port operations and regional shipping."}]
    except Exception as e:
        logger.debug(f"OpenWeather failed: {e}")
    return []


async def _fetch_noaa(query: str) -> list[dict]:
    """NOAA — climate & disaster data."""
    api_key = os.getenv("NOAA_API_KEY", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.ncdc.noaa.gov/cdo-web/api/v2/data",
                params={"datasetid": "GHCND", "locationid": "FIPS:US", "limit": 3, "startdate": "2025-01-01", "enddate": "2025-12-31"},
                headers={"token": api_key},
            )
            if resp.status_code == 200:
                return [{"title": "NOAA Climate Data", "url": "https://www.ncdc.noaa.gov", "snippet": "NOAA historical climate data accessed for logistics and disruption analysis."}]
    except Exception as e:
        logger.debug(f"NOAA failed: {e}")
    return []


async def _fetch_gdelt(query: str) -> list[dict]:
    """GDELT — global events and geopolitical signals (free, no key)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            encoded = query[:80].replace(" ", "%20")
            resp = await client.get(
                f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded}&mode=artlist&maxrecords=5&format=json",
                headers={"User-Agent": "SupplyChainGPT/1.0"},
            )
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                return [{"title": a.get("title", ""), "url": a.get("url", ""), "snippet": f"GDELT: Tone={a.get('tone', 'N/A')}, Source={a.get('domain', '')}. {a.get('title', '')}"}
                        for a in articles[:3]]
    except Exception as e:
        logger.debug(f"GDELT failed: {e}")
    return []


async def _fetch_frankfurter(query: str) -> list[dict]:
    """Frankfurter — ECB forex rates (free, no key)."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get("https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CNY,KRW,INR")
            if resp.status_code == 200:
                rates = resp.json().get("rates", {})
                snippet = "Current ECB forex rates (USD base): " + ", ".join([f"{k}={v}" for k, v in list(rates.items())[:6]])
                return [{"title": "ECB Forex Rates (Frankfurter)", "url": "https://www.frankfurter.app", "snippet": snippet}]
    except Exception as e:
        logger.debug(f"Frankfurter failed: {e}")
    return []


async def _fetch_nvd(query: str) -> list[dict]:
    """NIST NVD — cyber vulnerabilities affecting supply chain systems."""
    api_key = os.getenv("NIST_NVD_API_KEY", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params={"keywordSearch": "supply chain", "resultsPerPage": 3},
                headers={"apiKey": api_key},
            )
            if resp.status_code == 200:
                vulns = resp.json().get("vulnerabilities", [])
                results = []
                for v in vulns[:3]:
                    cve = v.get("cve", {})
                    cve_id = cve.get("id", "")
                    desc = cve.get("descriptions", [{}])[0].get("value", "")[:200]
                    results.append({"title": f"CVE: {cve_id}", "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}", "snippet": desc})
                return results
    except Exception as e:
        logger.debug(f"NVD failed: {e}")
    return []


async def _fetch_graphhopper(query: str) -> list[dict]:
    """GraphHopper — route/logistics data."""
    api_key = os.getenv("GRAPHHOPPER_API_KEY", "")
    if not api_key:
        return []
    try:
        # Geocode a relevant location from query
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://graphhopper.com/api/1/geocode",
                params={"q": "Shanghai Port", "key": api_key, "limit": 1},
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    h = hits[0]
                    return [{"title": "GraphHopper: Shanghai Port Location", "url": "https://www.graphhopper.com",
                             "snippet": f"Coordinates: {h.get('point', {})}. Name: {h.get('name', '')}. Logistics routing reference for trade route analysis."}]
    except Exception as e:
        logger.debug(f"GraphHopper failed: {e}")
    return []


# ── RAG fetch ─────────────────────────────────────────────────────────────────
async def _fetch_rag(agent_key: str, query: str) -> list[dict]:
    """Query the RAG pipeline for relevant internal knowledge base chunks."""
    try:
        from backend.rag.agent_rag_integration import get_rag_context
        ctx = await get_rag_context(agent_key, query, include_graph=False)
        if ctx and len(ctx) > 50:
            return [{"title": "Internal Knowledge Base (RAG)", "url": "rag://internal", "snippet": ctx[:600]}]
    except Exception as e:
        logger.debug(f"RAG gather failed for {agent_key}: {e}")
    return []


# ── Main gather function ───────────────────────────────────────────────────────
_API_MAP = {
    "gnews": _fetch_gnews,
    "marketaux": _fetch_marketaux,
    "alpha_vantage": _fetch_alpha_vantage,
    "openweather": _fetch_openweather,
    "noaa": _fetch_noaa,
    "gdelt": _fetch_gdelt,
    "frankfurter": _fetch_frankfurter,
    "nvd": _fetch_nvd,
    "graphhopper": _fetch_graphhopper,
}


async def gather_agent_data(agent_key: str, query: str) -> CitationBundle:
    """Gather real-time data for a specific agent and query. Returns CitationBundle.

    Strategy:
      1. Run 3 DuckDuckGo searches in parallel (agent-specific query templates)
      2. Scrape top 2 DDG URLs via Firecrawl
      3. Hit 3-4 domain-specific APIs in parallel
      4. Query RAG pipeline
      5. Build numbered citation list (min 9)
    """
    bundle = CitationBundle()
    citation_num = 1

    # 1. Build DuckDuckGo queries for this agent
    templates = AGENT_SEARCH_QUERIES.get(agent_key, AGENT_SEARCH_QUERIES["risk"])
    ddg_queries = [t.replace("{query}", query) for t in templates]

    # Run DDG searches in parallel
    ddg_tasks = [_ddg_search(q, max_results=4) for q in ddg_queries]
    ddg_results_nested = await asyncio.gather(*ddg_tasks, return_exceptions=True)

    # Flatten and deduplicate DDG results
    seen_urls = set()
    ddg_flat = []
    for results in ddg_results_nested:
        if isinstance(results, list):
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    ddg_flat.append(r)

    # Add up to 5 DDG citations
    scraped_urls = []
    for r in ddg_flat[:5]:
        bundle.citations.append(Citation(
            number=citation_num,
            source="DuckDuckGo Search",
            title=r.get("title", "Web Result"),
            url=r.get("url", ""),
            snippet=r.get("snippet", ""),
        ))
        scraped_urls.append(r.get("url", ""))
        citation_num += 1

    # 2. Firecrawl scrape top 2 URLs for deeper content
    scrape_tasks = [_firecrawl_scrape(url) for url in scraped_urls[:2] if url.startswith("http")]
    scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

    for url, content in zip(scraped_urls[:2], scrape_results):
        if isinstance(content, str) and content and len(content) > 100:
            # Find the matching DDG citation and enrich it, or add a new one
            enriched = False
            for c in bundle.citations:
                if c.url == url:
                    c.snippet = content[:600]  # Replace with richer scraped text
                    c.source = "Firecrawl + DuckDuckGo"
                    enriched = True
                    break
            if not enriched:
                bundle.citations.append(Citation(
                    number=citation_num,
                    source="Firecrawl Web Scrape",
                    title=f"Scraped: {url[:60]}",
                    url=url,
                    snippet=content[:600],
                ))
                citation_num += 1

    # 3. Real API sources for this agent (run in parallel)
    api_names = AGENT_API_SOURCES.get(agent_key, ["gnews", "gdelt"])
    api_tasks = [_API_MAP[name](query) for name in api_names if name in _API_MAP]
    api_results_nested = await asyncio.gather(*api_tasks, return_exceptions=True)

    for api_name, results in zip(api_names, api_results_nested):
        if isinstance(results, list):
            for r in results[:2]:  # max 2 per API
                if r.get("snippet"):
                    bundle.citations.append(Citation(
                        number=citation_num,
                        source=api_name.replace("_", " ").title(),
                        title=r.get("title", api_name),
                        url=r.get("url", ""),
                        snippet=r.get("snippet", ""),
                    ))
                    citation_num += 1

    # 4. RAG pipeline
    rag_results = await _fetch_rag(agent_key, query)
    for r in rag_results:
        bundle.citations.append(Citation(
            number=citation_num,
            source="RAG Knowledge Base",
            title=r.get("title", "Internal RAG"),
            url=r.get("url", "rag://internal"),
            snippet=r.get("snippet", ""),
        ))
        citation_num += 1

    logger.info(f"[{agent_key}] Gathered {len(bundle.citations)} citations for query: {query[:60]}")

    # 5. Ensure minimum 9 citations — pad with additional DDG if needed
    if len(bundle.citations) < 9:
        needed = 9 - len(bundle.citations)
        extra_query = f"supply chain {agent_key} analysis {query}"
        extra_results = await _ddg_search(extra_query, max_results=needed + 2)
        for r in extra_results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                bundle.citations.append(Citation(
                    number=citation_num,
                    source="DuckDuckGo Search",
                    title=r.get("title", "Web Result"),
                    url=url,
                    snippet=r.get("snippet", ""),
                ))
                citation_num += 1
                if len(bundle.citations) >= 9:
                    break

    # Re-number sequentially (some may have been re-ordered)
    for i, c in enumerate(bundle.citations, 1):
        c.number = i

    return bundle


async def gather_all_agents(query: str, agent_keys: list[str] | None = None) -> dict[str, CitationBundle]:
    """Pre-fetch data for all 6 agents in parallel.
    
    Args:
        query: The search query
        agent_keys: Optional list of specific agent keys to gather. If None, gathers for all 6 agents.
    """
    if agent_keys is None:
        agent_keys = ["risk", "supply", "logistics", "market", "finance", "brand"]
    tasks = [gather_agent_data(key, query) for key in agent_keys]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    bundles = {}
    for key, result in zip(agent_keys, results):
        if isinstance(result, CitationBundle):
            bundles[key] = result
        else:
            logger.error(f"Data gather failed for {key}: {result}")
            bundles[key] = CitationBundle()

    return bundles
