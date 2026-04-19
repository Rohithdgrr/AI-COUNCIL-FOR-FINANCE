"""
Lite Mode Subagent Runner

Runs 5 hybrid subagents (RAG, API, Web, MCP, Graph) in parallel
for a given parent agent. Each subagent combines a data-source
channel with parent-agent domain expertise.

Only used in lite mode — not in full council debate.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from backend.agents.subagent_registry import (
    SubagentDef,
    SUBAGENT_REGISTRY,
    SUBAGENT_CHANNELS,
)
from backend.state import SubagentEvidence

logger = logging.getLogger(__name__)


def _parse_confidence(text: str, default: int = 50) -> int:
    """Extract confidence score from LLM output text."""
    for pattern in [
        r"confidence\s*score\s*[:\s]*(\d{1,3})",
        r"confidence\s*[:\s]*(\d{1,3})",
        r"(\d{1,3})\s*/\s*100",
        r"(\d{1,3})\s*%\s*confidence",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            v = int(m.group(1))
            return min(v, 100)
    return default


def _detect_flags(text: str, confidence: int) -> list[str]:
    """Detect evidence flags from output text."""
    flags: list[str] = []
    lower = text.lower()
    if "contradiction" in lower or "conflict" in lower:
        flags.append("contradiction")
    if "verify" in lower or "unconfirmed" in lower:
        flags.append("needs_verification")
    if confidence < 40:
        flags.append("low_confidence")
    return flags


def _extract_source_refs(context_text: str) -> list[str]:
    """Extract [N] citation references from context."""
    return list(dict.fromkeys(re.findall(r"\[\d+\]", context_text)))


def _extract_links(context_text: str) -> list[str]:
    """Extract URLs from context."""
    return list(dict.fromkeys(re.findall(r"https?://\S+", context_text)))


async def run_subagent(
    subagent_def: SubagentDef,
    query: str,
    citation_context: str,
    parent_agent: str,
) -> SubagentEvidence:
    """Run a single subagent and return structured evidence.

    Args:
        subagent_def: Subagent definition from registry
        query: The original user query
        citation_context: Formatted citation context for this channel
        parent_agent: Parent agent key (e.g. "risk")

    Returns:
        SubagentEvidence with structured findings
    """
    from backend.llm.router import llm_router

    # Build domain-specific system prompt
    system_prompt = subagent_def["system_prompt_template"].format(
        parent_agent=parent_agent,
        domain_hint=subagent_def["domain_hint"],
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Inject citation context if available
    # NOTE: Do not aggressively truncate here; subagents must have enough context
    # to produce complete evidence summaries.
    if citation_context:
        messages.append({
            "role": "system",
            "content": f"Research data for analysis:\n\n{citation_context[:12000]}",
        })

    # Inject MCP tool descriptions for MCP channel
    if subagent_def["data_channel"] == "mcp":
        try:
            from backend.mcp.agent_mcp_integration import inject_mcp_system_prompt
            messages = inject_mcp_system_prompt(messages, parent_agent)
        except Exception:
            pass

    messages.append({
        "role": "user",
        "content": (
            f"Query: {query}\n\n"
            f"Analyze the above data from the perspective of {subagent_def['domain_hint']}. "
            f"Provide your evidence summary with inline citations [N] and a confidence score."
        ),
    })

    # Call LLM
    try:
        response_text = ""
        async for token in llm_router.stream_with_fallback(parent_agent, messages):
            response_text += token
    except Exception as e:
        # If streaming fails, try non-streaming invocation as a fallback.
        logger.error(f"Subagent {subagent_def['key']} LLM stream failed: {e}")
        try:
            response, _model_key = await llm_router.invoke_with_fallback(parent_agent, messages)
            response_text = getattr(response, "content", None) or str(response)
        except Exception as e2:
            logger.error(f"Subagent {subagent_def['key']} LLM invoke failed: {e2}")
            response_text = f"Evidence gathering failed: {e2}"

    # Parse results
    confidence = _parse_confidence(response_text)
    flags = _detect_flags(response_text, confidence)
    source_refs = _extract_source_refs(citation_context)[:10]
    links = _extract_links(citation_context)[:8]

    return SubagentEvidence(
        subagent_key=subagent_def["key"],
        parent_agent=parent_agent,
        data_channel=subagent_def["data_channel"],
        domain_hint=subagent_def["domain_hint"][:200],
        summary=response_text if response_text else "No evidence collected",
        sources=source_refs,
        confidence=confidence,
        flags=flags,
        links=links,
    )


async def run_all_subagents_streaming(
    parent_agent: str,
    query: str,
    citation_bundles: dict[str, object],
    policy: Optional[dict] = None,
    on_subagent_complete: Optional[callable] = None,
) -> list[SubagentEvidence]:
    """Run all 5 subagents for a parent agent in parallel and stream results as they complete.

    Args:
        parent_agent: Parent agent key (e.g. "risk")
        query: The original user query
        citation_bundles: Dict mapping data_channel → CitationBundle or context string
        policy: Optional support_agent_policy to gate channels
        on_subagent_complete: Optional callback when each subagent completes

    Returns:
        List of SubagentEvidence from all active subagents (complete results)
    """
    _default_policy = {"rag": True, "api": True, "mcp": True, "web": True, "graph": True}
    active_policy = policy or _default_policy

    subagent_defs = SUBAGENT_REGISTRY.get(parent_agent, [])
    if not subagent_defs:
        logger.warning(f"No subagent definitions found for {parent_agent}")
        return []

    # Filter by policy
    active_defs = [
        sd for sd in subagent_defs
        if active_policy.get(sd["data_channel"], True)
    ]

    if not active_defs:
        logger.warning(f"All subagent channels disabled for {parent_agent}")
        return []

    # Build citation context per channel
    async def _run_one(sd: SubagentDef) -> SubagentEvidence:
        channel = sd["data_channel"]
        # Try to get formatted context from citation bundle
        citation_context = ""
        bundle = citation_bundles.get(channel)
        if bundle:
            if hasattr(bundle, "format_context"):
                citation_context = bundle.format_context()
            elif isinstance(bundle, str):
                citation_context = bundle
            elif isinstance(bundle, dict):
                citation_context = str(bundle.get("context", ""))
        # Also try parent-level bundle (all channels combined)
        parent_bundle = citation_bundles.get(parent_agent)
        if not citation_context and parent_bundle:
            if hasattr(parent_bundle, "format_context"):
                citation_context = parent_bundle.format_context()

        return await run_subagent(sd, query, citation_context, parent_agent)

    # Run all active subagents in parallel with streaming
    tasks_map: dict[asyncio.Task, SubagentDef] = {}
    for sd in active_defs:
        task = asyncio.create_task(_run_one(sd))
        tasks_map[task] = sd

    evidence_list: list[SubagentEvidence] = []

    # Stream results as they complete
    for completed_task in asyncio.as_completed(tasks_map.keys()):
        try:
            result = await completed_task
            evidence_list.append(result)
            # Call callback if provided (for streaming SSE events)
            if on_subagent_complete:
                try:
                    await on_subagent_complete(result)
                except Exception as cb_err:
                    logger.error(f"Subagent complete callback failed: {cb_err}")
        except Exception as e:
            # Find which subagent failed
            failed_sd = None
            for task, sd in tasks_map.items():
                if task == completed_task:
                    failed_sd = sd
                    break
            if failed_sd:
                logger.error(f"Subagent {failed_sd['key']} failed: {e}")
                error_evidence = SubagentEvidence(
                    subagent_key=failed_sd["key"],
                    parent_agent=parent_agent,
                    data_channel=failed_sd["data_channel"],
                    domain_hint=failed_sd["domain_hint"][:200],
                    summary=f"Evidence gathering failed: {e}",
                    sources=[],
                    confidence=0,
                    flags=["error"],
                    links=[],
                )
                evidence_list.append(error_evidence)
                if on_subagent_complete:
                    try:
                        await on_subagent_complete(error_evidence)
                    except Exception as cb_err:
                        logger.error(f"Subagent error callback failed: {cb_err}")

    logger.info(
        f"Subagent streaming complete for {parent_agent}: "
        f"{len(evidence_list)} subagents, "
        f"avg_conf={sum(e.confidence for e in evidence_list) / max(len(evidence_list), 1):.0f}"
    )

    return evidence_list


# Keep backward-compatible alias
run_all_subagents = run_all_subagents_streaming


def subagent_evidence_to_support_evidence(
    subagent_results: list[SubagentEvidence],
) -> list[dict]:
    """Convert SubagentEvidence list to SupportEvidence-compatible dicts.

    Used for backward compatibility with existing EvidenceBundle construction.
    """
    from backend.state import SupportEvidence

    support_list: list[SupportEvidence] = []
    for se in subagent_results:
        support_list.append(SupportEvidence(
            agent=se.parent_agent,
            role=f"subagent:{se.data_channel}",
            summary=f"[{se.data_channel.upper()}] {se.summary[:400]}",
            sources=se.sources,
            confidence=se.confidence,
            flags=se.flags,
            links=se.links,
        ))
    return [s.model_dump() for s in support_list]
