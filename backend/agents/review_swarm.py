"""Review Swarm for SupplyChainGPT Council - Coordinates multiple reviewer agents.

Review agents validate main agent outputs before delivery:
- CritiqueAgent: Finds flaws and weaknesses
- ValidateAgent: Fact-checks against sources
- SynthesizeAgent: Combines critiques into actionable feedback

Inspired by MiroFish's multi-agent simulation approach, adapted for
supply chain council review/validation.
"""

import asyncio
import logging
import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)


class ReviewCritique(BaseModel):
    """A single critique from a review agent."""
    reviewer: str = Field(..., description="Reviewer agent name")
    role: str = Field(..., description="Reviewer role")
    severity: str = Field(default="medium", description="low/medium/high/critical")
    category: str = Field(default="accuracy", description="accuracy/completeness/relevance/bias/logic")
    finding: str = Field(..., description="What was found")
    suggestion: str = Field(default="", description="How to fix it")


class ReviewResult(BaseModel):
    """Aggregated review result from the swarm."""
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall quality score")
    critiques: List[ReviewCritique] = Field(default_factory=list)
    validated_facts: List[str] = Field(default_factory=list, description="Facts that were verified")
    unverified_claims: List[str] = Field(default_factory=list, description="Claims needing verification")
    improvements: List[str] = Field(default_factory=list, description="Suggested improvements")
    passed: bool = Field(default=True, description="Whether output passes review")


class ReviewSwarm:
    """Coordinates multiple review agents to validate agent outputs."""

    CRITIQUE_PROMPT = """You are a **Critical Reviewer** in a supply chain council. Your job is to find flaws, weaknesses, and gaps in the following agent output.

Agent: {agent_name}
Output:
{output}

Sources available:
{sources}

Identify issues in these categories:
- **Accuracy**: Are claims supported by sources or data?
- **Completeness**: Are there missing considerations or perspectives?
- **Relevance**: Is the output focused on the actual query?
- **Bias**: Is there unwarranted bias or one-sided analysis?
- **Logic**: Are there logical fallacies or unsupported leaps?

For each issue found, provide:
1. Severity (low/medium/high/critical)
2. Category (accuracy/completeness/relevance/bias/logic)
3. Finding (what's wrong)
4. Suggestion (how to fix)

Be thorough but fair. Not everything is wrong — focus on genuine issues.

Respond as JSON array:
[
  {{
    "severity": "medium",
    "category": "accuracy",
    "finding": "Claim X is not supported by sources",
    "suggestion": "Add source citation or soften the claim"
  }}
]"""

    VALIDATE_PROMPT = """You are a **Fact Validator** in a supply chain council. Your job is to verify claims against available sources.

Agent: {agent_name}
Claims to validate:
{claims}

Sources:
{sources}

For each claim, determine:
- Can it be verified from the sources?
- Is it partially true but missing context?
- Is it unsupported?

Respond as JSON:
{{
  "validated": ["claim that is fully supported"],
  "partially_validated": ["claim with some support but missing context"],
  "unverified": ["claim with no source support"],
  "corrections": ["specific correction needed"]
}}"""

    SYNTHESIZE_PROMPT = """You are a **Review Synthesizer** in a supply chain council. Combine the following critiques and validations into actionable feedback.

Critiques:
{critiques}

Validation results:
{validation}

Synthesize into:
1. Overall quality score (0.0 to 1.0)
2. Top 3 improvements needed (prioritized)
3. Whether the output passes review (score >= 0.6 = pass)

Respond as JSON:
{{
  "overall_score": 0.75,
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "passed": true
}}"""

    async def review_output(
        self,
        agent_name: str,
        output: str,
        sources: Optional[List[str]] = None,
        min_score: float = 0.6,
    ) -> ReviewResult:
        """Run the full review swarm on an agent output.

        All three reviewers run in parallel for speed.

        Args:
            agent_name: Name of the agent being reviewed
            output: The agent's output text
            sources: Available source texts
            min_score: Minimum score to pass review

        Returns:
            Aggregated ReviewResult
        """
        logger.info(f"Review swarm starting for agent: {agent_name}")
        sources_text = "\n".join(sources[:10]) if sources else "No sources available"

        # Run critique and validation in parallel
        critique_task = self._run_critique(agent_name, output, sources_text)
        validate_task = self._run_validation(agent_name, output, sources_text)

        critiques, validation = await asyncio.gather(critique_task, validate_task)

        # Synthesize results
        result = await self._synthesize(critiques, validation, min_score)

        logger.info(
            f"Review swarm complete for {agent_name}: "
            f"score={result.overall_score:.2f}, passed={result.passed}, "
            f"{len(result.critiques)} critiques"
        )
        return result

    async def _run_critique(
        self,
        agent_name: str,
        output: str,
        sources_text: str,
    ) -> List[ReviewCritique]:
        """Run the critique agent."""
        prompt = self.CRITIQUE_PROMPT.format(
            agent_name=agent_name,
            output=output[:3000],
            sources=sources_text[:2000],
        )

        try:
            messages = [
                {"role": "system", "content": "You are a critical reviewer for supply chain analysis. Find genuine issues, not nitpicks."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                data = json.loads(json_match.group())
                critiques = []
                for item in data:
                    critiques.append(ReviewCritique(
                        reviewer="critique_agent",
                        role="critic",
                        severity=item.get("severity", "medium"),
                        category=item.get("category", "accuracy"),
                        finding=item.get("finding", ""),
                        suggestion=item.get("suggestion", ""),
                    ))
                return critiques
        except Exception as e:
            logger.error(f"Critique agent failed: {e}")

        return []

    async def _run_validation(
        self,
        agent_name: str,
        output: str,
        sources_text: str,
    ) -> dict:
        """Run the validation agent."""
        # Extract key claims from output
        claims = self._extract_claims(output)

        prompt = self.VALIDATE_PROMPT.format(
            agent_name=agent_name,
            claims="\n".join(f"- {c}" for c in claims[:10]),
            sources=sources_text[:2000],
        )

        try:
            messages = [
                {"role": "system", "content": "You are a fact-checker for supply chain analysis. Verify claims against sources."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Validation agent failed: {e}")

        return {"validated": [], "partially_validated": [], "unverified": [], "corrections": []}

    async def _synthesize(
        self,
        critiques: List[ReviewCritique],
        validation: dict,
        min_score: float,
    ) -> ReviewResult:
        """Synthesize critiques and validation into final review result."""
        critiques_text = "\n".join(
            f"[{c.severity}] {c.category}: {c.finding} → {c.suggestion}"
            for c in critiques
        )
        validation_text = json.dumps(validation, indent=2)

        prompt = self.SYNTHESIZE_PROMPT.format(
            critiques=critiques_text or "No critiques found",
            validation=validation_text,
        )

        try:
            messages = [
                {"role": "system", "content": "You are a review synthesizer. Combine critiques into actionable feedback."},
                {"role": "user", "content": prompt},
            ]

            response, _ = await llm_router.invoke_with_fallback("moderator", messages)
            content = getattr(response, "content", str(response))

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                score = data.get("overall_score", 0.5)
                return ReviewResult(
                    overall_score=score,
                    critiques=critiques,
                    validated_facts=validation.get("validated", []),
                    unverified_claims=validation.get("unverified", []),
                    improvements=data.get("improvements", []),
                    passed=score >= min_score,
                )
        except Exception as e:
            logger.error(f"Synthesis agent failed: {e}")

        # Fallback: compute score from critiques
        severity_weights = {"low": 0.05, "medium": 0.1, "high": 0.2, "critical": 0.4}
        penalty = sum(severity_weights.get(c.severity, 0.1) for c in critiques)
        score = max(0.0, min(1.0, 1.0 - penalty))

        return ReviewResult(
            overall_score=score,
            critiques=critiques,
            validated_facts=validation.get("validated", []),
            unverified_claims=validation.get("unverified", []),
            improvements=[c.suggestion for c in critiques if c.suggestion],
            passed=score >= min_score,
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Extract key claims from agent output for validation."""
        # Split into sentences and filter for claim-like statements
        sentences = re.split(r'[.!?]\s+', text)
        claims = []
        for s in sentences:
            s = s.strip()
            # Look for sentences with numbers, percentages, or assertive language
            if (re.search(r'\d+%|\$\d+|\d+\s*(million|billion|units|days)', s) or
                any(w in s.lower() for w in ['will', 'expect', 'forecast', 'predict', 'estimate', 'increase', 'decrease', 'risk'])):
                claims.append(s)
        return claims[:15]
