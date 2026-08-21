"""Debate Engine for SupplyChainGPT Council.

Implements a 3-round structured debate using LangGraph:
  - Round 1: Parallel Analysis (all agents contribute independently)
  - Round 2: Challenge & Counter (agents critique each other's positions)
  - Round 3: Validation & Synthesis (final convergence or forced decision)

Features:
  - Confidence-weighted consensus logic
  - Max 3 rounds to prevent infinite loops
  - Full debate_history stored in CouncilState
  - Structured Pydantic outputs (DebateRound) for every round
  - Human-in-the-loop interrupt before final synthesis
  - LangSmith tracing on every round
  - RAG + MCP data grounding to prevent hallucinations
"""

import json
import logging
from typing import Optional

import time as _time

from backend.state import CouncilState, AgentOutput, DebateRound
from backend.llm.router import llm_router
from backend.utils.parsing import parse_confidence
from backend.observability.langsmith_config import (
    CouncilTracer, record_debate_round, record_agent_call,
)

logger = logging.getLogger(__name__)

MAX_DEBATE_ROUNDS = 3
CONSENSUS_THRESHOLD = 15.0  # max confidence gap for consensus
SELF_CRITIQUE_PROMPT_TEMPLATE = """You are the {agent_name} agent reviewing your own analysis.

Your original analysis:
{own_contribution}

Critically examine your own position:
1. What assumptions might be wrong?
2. What data gaps exist in your analysis?
3. What alternative interpretations could exist?
4. How could your confidence level change with better data?
5. Your revised confidence (0-100) after self-critique

Be honest and rigorous. Self-awareness improves the council's decision quality.
"""

CHALLENGE_PROMPT_TEMPLATE = """You are the {challenger_agent} agent challenging the {target_agent} agent's position.

{target_agent}'s position:
{target_contribution}

Your original position:
{challenger_contribution}

Your self-critique findings:
{challenger_self_critique}

Challenge their key assumptions, data sources, or risk assessments. Be specific.
If you agree with parts of their analysis, acknowledge those points.
Ground your challenge in the retrieved context and MCP data provided.
Incorporate your self-critique to strengthen your challenge.

Respond with:
1. Points of agreement
2. Specific challenges (with evidence)
3. Suggested compromise position
4. Your updated confidence (0-100)
"""

SYNTHESIS_PROMPT = """You are the Council Moderator synthesizing the final debate outcome.

Original Query: {query}

Debate History:
{debate_summary}

Agent Consensus Points: {consensus_points}
Key Disagreements: {disagreements}

Synthesize the final recommendation:
1. Unified recommendation with priority actions
2. Confidence-weighted decision rationale
3. Fallback options (Tier 1: Immediate, Tier 2: Short-term, Tier 3: Strategic)
4. Key disagreements that could not be resolved
5. Overall council confidence score (0-100)
6. Risk score (0-100)
"""


class DebateEngine:
    """Orchestrates multi-round structured debate between council agents.

    Each round produces a DebateRound with structured output.
    The engine tracks confidence convergence and stops early if
    agents reach consensus (gap < CONSENSUS_THRESHOLD).

    Features:
      - Self-critique: agents review their own analysis before challenging others
      - Lite mode: skip Round 2 for faster verdicts
      - Configurable rounds, consensus threshold, and self-critique toggle
    """

    def __init__(
        self,
        max_rounds: int = MAX_DEBATE_ROUNDS,
        consensus_threshold: float = CONSENSUS_THRESHOLD,
        lite_mode: bool = False,
        enable_self_critique: bool = True,
    ):
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.lite_mode = lite_mode
        self.enable_self_critique = enable_self_critique

    async def run_debate(self, state: CouncilState) -> dict:
        """Execute the full debate cycle and return state updates.

        Returns dict with:
          - debate_rounds: list of DebateRound dicts
          - round_number: final round number
          - confidence: final council confidence
          - risk_score: computed risk score
          - recommendation: final synthesized recommendation
          - fallback_options: tiered fallback actions
        """
        agent_outputs = state.get("agent_outputs", [])
        query = state.get("query", "")
        context = state.get("context") or {}
        session_id = state.get("session_id", "unknown")

        if not agent_outputs:
            return {
                "debate_rounds": [],
                "round_number": state.get("round_number", 1),
                "confidence": 0.0,
                "risk_score": 0.0,
                "recommendation": "No agent outputs to debate.",
                "fallback_options": [],
            }

        tracer = CouncilTracer(session_id)
        all_rounds = []
        current_outputs = list(agent_outputs)

        # Round 1: Parallel Analysis (already done by agents — summarize)
        t0 = _time.monotonic()
        with tracer.trace_debate_round(1, phase="analysis"):
            round1 = await self._round_analysis(current_outputs, query, context)
        latency1 = (_time.monotonic() - t0) * 1000
        record_debate_round(session_id, 1, "analysis", round1["round_confidence"], 0, latency1)
        all_rounds.append(round1)

        # Check if consensus already reached
        if round1["round_confidence"] >= (100 - self.consensus_threshold):
            logger.info("Consensus reached after Round 1 — skipping further rounds")
            return await self._finalize(all_rounds, current_outputs, query, state, tracer)

        # Self-critique: agents review their own analysis before challenging others
        self_critiques = {}
        if self.enable_self_critique:
            t0 = _time.monotonic()
            with tracer.trace_debate_round(1, phase="self_critique"):
                self_critiques = await self._round_self_critique(current_outputs, query, context)
            latency_sc = (_time.monotonic() - t0) * 1000
            record_debate_round(session_id, 1, "self_critique", round1["round_confidence"], 0, latency_sc)
            logger.info(f"Self-critique complete for {len(self_critiques)} agents")

        # Lite mode: skip Round 2 (challenge phase) for faster verdict
        if self.lite_mode:
            logger.info("Lite mode enabled — skipping Round 2 challenge phase")
            return await self._finalize(all_rounds, current_outputs, query, state, tracer)

        # Round 2: Challenge & Counter
        t0 = _time.monotonic()
        with tracer.trace_debate_round(2, phase="challenge"):
            round2 = await self._round_challenge(current_outputs, query, context, self_critiques)
        latency2 = (_time.monotonic() - t0) * 1000
        record_debate_round(session_id, 2, "challenge", round2["round_confidence"], 0, latency2)
        all_rounds.append(round2)

        # Update outputs with challenged positions
        current_outputs = self._merge_challenge_results(current_outputs, round2)

        if round2["round_confidence"] >= (100 - self.consensus_threshold):
            logger.info("Consensus reached after Round 2 — skipping Round 3")
            return await self._finalize(all_rounds, current_outputs, query, state, tracer)

        # Round 3: Validation & Synthesis
        t0 = _time.monotonic()
        with tracer.trace_debate_round(3, phase="validation"):
            round3 = await self._round_validation(current_outputs, query, context)
        latency3 = (_time.monotonic() - t0) * 1000
        record_debate_round(session_id, 3, "validation", round3["round_confidence"], 0, latency3)
        all_rounds.append(round3)

        return await self._finalize(all_rounds, current_outputs, query, state, tracer)

    # -----------------------------------------------------------------------
    # Round 1: Parallel Analysis Summary
    # -----------------------------------------------------------------------
    async def _round_analysis(self, outputs: list[AgentOutput], query: str, context: dict) -> dict:
        """Summarize the parallel analysis round from agent outputs."""
        contributions = []
        for o in outputs:
            contributions.append({
                "agent": o.agent,
                "point": o.contribution[:500],
                "confidence": o.confidence,
                "challenges": [],
            })

        confidences = [o.confidence for o in outputs if o.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Extract key disagreements and consensus via LLM
        disagreements, consensus = await self._extract_positions(outputs, query, context)

        return DebateRound(
            round_number=1,
            phase="analysis",
            agent_contributions=contributions,
            key_disagreements=disagreements,
            consensus_points=consensus,
            round_confidence=round(avg_confidence, 1),
        ).model_dump()

    # -----------------------------------------------------------------------
    # Self-Critique Round (between Round 1 and Round 2)
    # -----------------------------------------------------------------------
    async def _round_self_critique(self, outputs: list[AgentOutput], query: str, context: dict) -> dict[str, str]:
        """Each agent critiques its own analysis before challenging others.

        Returns dict mapping agent name -> self-critique text.
        """
        critiques = {}
        import asyncio

        async def _critique_one(agent_output: AgentOutput) -> tuple[str, str]:
            rag_ctx = ""
            mcp_ctx = ""
            if context:
                rag_contexts = context.get("rag_contexts") or {}
                mcp_contexts = context.get("mcp_contexts") or {}
                rag_ctx = rag_contexts.get(agent_output.agent, "")
                mcp_ctx = mcp_contexts.get(agent_output.agent, "")

            prompt = SELF_CRITIQUE_PROMPT_TEMPLATE.format(
                agent_name=agent_output.agent.upper(),
                own_contribution=agent_output.contribution[:1000],
            )

            context_section = ""
            if rag_ctx:
                context_section += f"\n\nRetrieved Context:\n{rag_ctx[:1000]}"
            if mcp_ctx:
                context_section += f"\n\nMCP Data:\n{mcp_ctx[:1000]}"

            messages = [
                {"role": "system", "content": prompt + context_section},
                {"role": "user", "content": f"Critique your own analysis of: {query}"},
            ]

            try:
                response, model_used = await llm_router.invoke_with_fallback(agent_output.agent, messages)
                return (agent_output.agent, response.content)
            except Exception as e:
                logger.warning(f"Self-critique for {agent_output.agent} failed: {e}")
                return (agent_output.agent, f"Self-critique unavailable: {e}")

        # Run all self-critiques in parallel
        results = await asyncio.gather(*[_critique_one(o) for o in outputs])
        for agent_name, critique_text in results:
            critiques[agent_name] = critique_text

        return critiques

    # -----------------------------------------------------------------------
    # Round 2: Challenge & Counter
    # -----------------------------------------------------------------------
    async def _round_challenge(self, outputs: list[AgentOutput], query: str, context: dict, self_critiques: dict[str, str] | None = None) -> dict:
        """Each agent challenges the most conflicting other agent."""
        challenges = []
        if self_critiques is None:
            self_critiques = {}

        for i, challenger in enumerate(outputs):
            # Find the most conflicting agent (largest confidence gap)
            target = self._find_challenge_target(challenger, outputs)
            if not target:
                continue

            # Build challenge prompt with RAG/MCP context
            rag_ctx = ""
            mcp_ctx = ""
            if context:
                rag_contexts = context.get("rag_contexts") or {}
                mcp_contexts = context.get("mcp_contexts") or {}
                rag_ctx = rag_contexts.get(challenger.agent, "")
                mcp_ctx = mcp_contexts.get(challenger.agent, "")

            critique_text = self_critiques.get(challenger.agent, "No self-critique available.")
            prompt = CHALLENGE_PROMPT_TEMPLATE.format(
                challenger_agent=challenger.agent.upper(),
                target_agent=target.agent.upper(),
                target_contribution=target.contribution[:800],
                challenger_contribution=challenger.contribution[:800],
                challenger_self_critique=critique_text[:600],
            )

            context_section = ""
            if rag_ctx:
                context_section += f"\n\nRetrieved Context:\n{rag_ctx[:1000]}"
            if mcp_ctx:
                context_section += f"\n\nMCP Data:\n{mcp_ctx[:1000]}"

            messages = [
                {"role": "system", "content": prompt + context_section},
                {"role": "user", "content": f"Challenge {target.agent.upper()}'s position on: {query}"},
            ]

            try:
                response, model_used = await llm_router.invoke_with_fallback(challenger.agent, messages)
                # Parse updated confidence from response
                updated_conf = parse_confidence(response.content, challenger.confidence)

                challenges.append({
                    "agent": challenger.agent,
                    "challenged": target.agent,
                    "challenge": response.content[:500],
                    "updated_confidence": updated_conf,
                    "model_used": model_used,
                })
            except Exception as e:
                logger.warning(f"Challenge from {challenger.agent} failed: {e}")
                challenges.append({
                    "agent": challenger.agent,
                    "challenged": target.agent,
                    "challenge": f"Challenge failed: {e}",
                    "updated_confidence": challenger.confidence,
                    "model_used": "error",
                })

        # Compute round metrics
        updated_confidences = [c["updated_confidence"] for c in challenges]
        avg_conf = sum(updated_confidences) / len(updated_confidences) if updated_confidences else 0

        disagreements, consensus = await self._extract_positions_from_challenges(challenges, query)

        return DebateRound(
            round_number=2,
            phase="challenge",
            agent_contributions=challenges,
            key_disagreements=disagreements,
            consensus_points=consensus,
            round_confidence=round(avg_conf, 1),
        ).model_dump()

    # -----------------------------------------------------------------------
    # Round 3: Validation & Synthesis
    # -----------------------------------------------------------------------
    async def _round_validation(self, outputs: list[AgentOutput], query: str, context: dict) -> dict:
        """Final validation round — agents confirm or adjust their positions."""
        contributions = []
        for o in outputs:
            contributions.append({
                "agent": o.agent,
                "point": o.contribution[:300],
                "confidence": o.confidence,
                "challenges": [],
            })

        confidences = [o.confidence for o in outputs if o.confidence > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        # Force consensus extraction
        disagreements, consensus = await self._extract_positions(outputs, query, context)

        return DebateRound(
            round_number=3,
            phase="validation",
            agent_contributions=contributions,
            key_disagreements=disagreements,
            consensus_points=consensus,
            round_confidence=round(avg_conf, 1),
        ).model_dump()

    # -----------------------------------------------------------------------
    # Final synthesis
    # -----------------------------------------------------------------------
    async def _finalize(self, rounds: list[dict], outputs: list[AgentOutput], query: str, state: CouncilState, tracer: CouncilTracer = None) -> dict:
        """Synthesize final recommendation from debate rounds."""
        debate_summary = self._format_debate_summary(rounds)
        last_round = rounds[-1]

        consensus_points = last_round.get("consensus_points", [])
        disagreements = last_round.get("key_disagreements", [])

        # Build synthesis prompt
        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            debate_summary=debate_summary,
            consensus_points=json.dumps(consensus_points, indent=2),
            disagreements=json.dumps(disagreements, indent=2),
        )

        messages = [{"role": "system", "content": prompt}]

        # Inject RAG context for moderator
        context = state.get("context") or {}
        rag_contexts = context.get("rag_contexts") or {}
        moderator_rag = rag_contexts.get("moderator", "")
        if moderator_rag:
            from backend.rag.agent_rag_integration import inject_rag_into_messages
            messages = inject_rag_into_messages(messages, moderator_rag)

        messages.append({"role": "user", "content": f"Synthesize final recommendation for: {query}"})

        t0 = _time.monotonic()
        try:
            with (tracer.trace_debate_round(0, phase="synthesis") if tracer else _null_ctx()):
                response, model_used = await llm_router.invoke_with_fallback("moderator", messages)
            recommendation = response.content
            # Parse confidence and risk from response
            final_confidence = parse_confidence(response.content, last_round.get("round_confidence", 50))
            risk_score = self._parse_risk_score(response.content, 50)
        except Exception as e:
            logger.error(f"Final synthesis failed: {e}")
            recommendation = f"Synthesis failed: {e}"
            final_confidence = last_round.get("round_confidence", 0)
            risk_score = 50
        latency_ms = (_time.monotonic() - t0) * 1000
        if tracer:
            record_debate_round(state.get("session_id", ""), 0, "synthesis", final_confidence, risk_score, latency_ms)

        # Generate fallback options from debate
        fallbacks = self._generate_fallbacks(outputs, risk_score)

        return {
            "debate_rounds": rounds,
            "round_number": len(rounds) + 1,
            "confidence": final_confidence / 100.0,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "fallback_options": fallbacks,
            "debate_history": [
                {"round": r["round_number"], "phase": r["phase"], "confidence": r["round_confidence"]}
                for r in rounds
            ],
        }

    # -----------------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------------
    def _find_challenge_target(self, challenger: AgentOutput, all_outputs: list[AgentOutput]) -> Optional[AgentOutput]:
        """Find the agent whose confidence differs most from the challenger.

        If all agents have the same confidence, pick the next agent in the list
        to ensure a challenge always occurs.
        """
        best_target = None
        max_gap = 0

        for o in all_outputs:
            if o.agent == challenger.agent:
                continue
            gap = abs(o.confidence - challenger.confidence)
            if gap > max_gap:
                max_gap = gap
                best_target = o

        # If all agents have same confidence, pick the next agent for a challenge
        if best_target is None:
            for o in all_outputs:
                if o.agent != challenger.agent:
                    return o

        return best_target

    def _parse_risk_score(self, text: str, default: float) -> float:
        """Extract risk score from LLM response text."""
        import re
        patterns = [
            r"risk\s+score[:\s]+(\d+(?:\.\d+)?)",
            r"risk[:\s]+(\d+(?:\.\d+)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                return min(val, 100.0) if val > 1 else val * 100
        return default

    async def _extract_positions(self, outputs: list[AgentOutput], query: str, context: dict) -> tuple[list[str], list[str]]:
        """Use LLM to extract key disagreements and consensus from agent outputs."""
        agent_summaries = "\n".join([
            f"- {o.agent.upper()} (confidence {o.confidence}%): {o.contribution[:300]}"
            for o in outputs
        ])

        messages = [
            {"role": "system", "content": "Extract key disagreements and consensus points from these agent analyses. Return JSON: {\"disagreements\": [...], \"consensus\": [...] }"},
            {"role": "user", "content": f"Query: {query}\n\nAgent Analyses:\n{agent_summaries}"},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = response.content
            # Try to parse JSON — handle markdown code block wrapping
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                disagreements = parsed.get("disagreements", [])
                consensus = parsed.get("consensus", [])
                # Coerce to strings (LLM may return dicts)
                disagreements = [json.dumps(d) if isinstance(d, dict) else str(d) for d in disagreements]
                consensus = [json.dumps(c) if isinstance(c, dict) else str(c) for c in consensus]
                return disagreements, consensus
            # No JSON found — fall through to heuristic
        except Exception as e:
            logger.warning(f"Position extraction LLM call failed: {e}")

        # Fallback: simple heuristic based on confidence spread
        confidences = [o.confidence for o in outputs]
        gap = max(confidences) - min(confidences) if confidences else 0
        disagreements = [f"Confidence gap of {gap:.0f}% between agents"] if gap > 20 else []
        consensus = ["All agents agree action is needed"] if gap <= 20 else []
        return disagreements, consensus

    async def _extract_positions_from_challenges(self, challenges: list[dict], query: str) -> tuple[list[str], list[str]]:
        """Extract positions from challenge round results using LLM."""
        if not challenges:
            return [], []

        challenge_summaries = "\n".join([
            f"- {c.get('agent', '?')} challenges {c.get('challenged', '?')}: {c.get('challenge', '')[:300]}"
            for c in challenges
        ])

        messages = [
            {"role": "system", "content": "Extract key disagreements and consensus from these challenge results. Return JSON: {\"disagreements\": [...], \"consensus\": [...] }"},
            {"role": "user", "content": f"Query: {query}\n\nChallenges:\n{challenge_summaries}"},
        ]

        try:
            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                parsed = json.loads(json_match.group())
                disagreements = parsed.get("disagreements", [])[:5]
                consensus = parsed.get("consensus", [])[:5]
                disagreements = [json.dumps(d) if isinstance(d, dict) else str(d) for d in disagreements]
                consensus = [json.dumps(c) if isinstance(c, dict) else str(c) for c in consensus]
                return disagreements, consensus
        except Exception as e:
            logger.warning(f"Challenge position extraction failed: {e}")

        # Fallback: keyword matching
        disagreements = []
        consensus = []
        for c in challenges:
            challenge_text = c.get("challenge", "")
            if "disagree" in challenge_text.lower() or "challenge" in challenge_text.lower():
                disagreements.append(f"{c.get('agent', '?')} challenges {c.get('challenged', '?')}")
            if "agree" in challenge_text.lower():
                consensus.append(f"{c.get('agent', '?')} agrees with {c.get('challenged', '?')}")

        return disagreements[:5], consensus[:5]

    def _merge_challenge_results(self, outputs: list[AgentOutput], round2: dict) -> list[AgentOutput]:
        """Update agent outputs with challenge round confidence adjustments."""
        contributions = round2.get("agent_contributions", [])
        updated = list(outputs)

        for c in contributions:
            agent_name = c.get("agent", "")
            new_conf = c.get("updated_confidence", 0)
            for i, o in enumerate(updated):
                if o.agent == agent_name:
                    updated[i] = AgentOutput(
                        agent=o.agent,
                        confidence=new_conf,
                        contribution=o.contribution,
                        key_points=o.key_points,
                        model_used=o.model_used,
                        provider=o.provider,
                    )
                    break

        return updated

    def _format_debate_summary(self, rounds: list[dict]) -> str:
        """Format debate rounds into a readable summary for synthesis."""
        parts = []
        for r in rounds:
            parts.append(
                f"Round {r['round_number']} ({r['phase']}): "
                f"Confidence={r['round_confidence']}%, "
                f"Consensus={r.get('consensus_points', [])}, "
                f"Disagreements={r.get('key_disagreements', [])}"
            )
        return "\n".join(parts)

    def _generate_fallbacks(self, outputs: list[AgentOutput], risk_score: float) -> list[dict]:
        """Generate tiered fallback options based on debate output."""
        from backend.state import Action
        fallbacks = []

        if risk_score > 60:
            fallbacks.append(Action(
                type="tier1_immediate",
                details="Activate near-shoring backup suppliers and emergency inventory release",
                cost_estimate=150000,
                time_to_implement="3 days",
            ).model_dump())
            fallbacks.append(Action(
                type="tier2_shortterm",
                details="Diversify to 2+ alternative suppliers with safety stock buffer",
                cost_estimate=500000,
                time_to_implement="14 days",
            ).model_dump())

        if risk_score > 30:
            fallbacks.append(Action(
                type="tier3_strategic",
                details="Long-term dual-sourcing strategy with regional distribution hubs",
                cost_estimate=2000000,
                time_to_implement="90 days",
            ).model_dump())

        return fallbacks


class _null_ctx:
    """No-op context manager for optional tracer."""
    def __enter__(self): return self
    def __exit__(self, *a): pass


# ---------------------------------------------------------------------------
# Singleton instance — configured from application settings
# ---------------------------------------------------------------------------
try:
    from backend.config import settings as _settings
    debate_engine = DebateEngine(
        max_rounds=_settings.max_debate_rounds,
        consensus_threshold=_settings.confidence_gap_threshold,
        lite_mode=getattr(_settings, "council_lite_mode", False),
        enable_self_critique=getattr(_settings, "enable_self_critique", True),
    )
except Exception:
    debate_engine = DebateEngine()
