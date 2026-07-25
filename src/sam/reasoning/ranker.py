"""
Plan Ranker – Sprint 23 Fase 1

Ranks multiple PlanCandidates by a weighted scoring formula and
applies optional governance filtering to reject unsuitable plans.

Flow:
  1. Governance filter: reject plans that fail governance checks
  2. Score calculation: weighted composite of risk, confidence,
     historical success, duration, and approval requirement
  3. Sort by score (descending)
  4. Select best (highest score)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import structlog

from .candidate import PlanCandidate


logger = structlog.get_logger()


# ── Scoring Weights ──────────────────────────────────────────────────

# How each factor contributes to the final composite score (0.0–1.0).
# Values should sum to 1.0 for a normalised total.

WEIGHT_RISK: float = 0.30          # Lower risk → higher score
WEIGHT_CONFIDENCE: float = 0.30    # Higher confidence → higher score
WEIGHT_HISTORICAL: float = 0.20    # Higher historical success → higher score
WEIGHT_DURATION: float = 0.10      # Shorter duration → higher score
WEIGHT_APPROVAL: float = 0.10   # False (no approval needed) → higher score



class PlanRanker:
    """Ranks plan candidates by a weighted scoring formula.

    Governance integration:
    - Filters out candidates that would be rejected by governance.
    - Requires a ``governance_engine`` if governance filtering is used.
    """

    def __init__(
        self,
        governance_engine: Any = None,
    ) -> None:
        """Initialise the PlanRanker.

        Args:
            governance_engine: Optional GovernanceEngine for filtering.
                If not provided, ``apply_governance`` will be a no-op.
        """
        self._governance_engine = governance_engine
        self._logger = logger.bind(component="PlanRanker")

    # ── Public API ─────────────────────────────────────────────────

    async def rank(self, candidates: List[PlanCandidate]) -> List[PlanCandidate]:
        """Sort candidates by composite score (descending).

        Each candidate gets a ``_score`` attribute (set in-place
        for use by ``select_best``).

        Args:
            candidates: The list of candidates to rank.

        Returns:
            Candidates sorted by score, highest first. An empty list
            if candidates is empty.
        """
        if not candidates:
            return []

        scored: List[PlanCandidate] = []
        for c in candidates:
            score = self._calculate_score(c)
            c.metadata["_rank_score"] = score
            scored.append(c)

        scored.sort(key=lambda c: c.metadata.get("_rank_score", 0.0), reverse=True)

        # Log top-3
        for i, c in enumerate(scored[:3]):
            self._logger.debug(
                "rank.candidate",
                rank=i + 1,
                candidate_id=c.id,
                graph_name=c.graph.name,
                score=c.metadata.get("_rank_score", 0.0),
            )

        return scored

    async def select_best(self, candidates: List[PlanCandidate]) -> Optional[PlanCandidate]:
        """Return the highest-scoring candidate.

        Args:
            candidates: Ranked or unranked list of candidates.

        Returns:
            The candidate with the highest score, or None if empty.
        """
        if not candidates:
            return None

        # Rank if not already ranked
        if candidates[0].metadata.get("_rank_score") is None:
            candidates = await self.rank(candidates)

        return candidates[0] if candidates else None

    async def apply_governance(
        self,
        candidates: List[PlanCandidate],
    ) -> List[PlanCandidate]:
        """Filter out candidates that fail governance checks.

        Each candidate's graph is evaluated by the GovernanceEngine.
        Candidates that are REJECTED or ESCALATED are removed.

        Args:
            candidates: The list of candidates to filter.

        Returns:
            Filtered list of candidates that passed governance.
        """
        if not candidates:
            return []

        if self._governance_engine is None:
            # No governance engine — pass all through
            return candidates

        passed: List[PlanCandidate] = []
        for c in candidates:
            try:
                result = await self._governance_engine.evaluate(c.graph)
            except Exception as exc:
                self._logger.warning(
                    "governance.evaluate_failed",
                    candidate_id=c.id,
                    error=str(exc),
                )
                continue

            decision = getattr(result, "decision", None)
            decision_str = str(getattr(decision, "value", decision))

            if decision_str in ("REJECT", "ESCALATE"):
                self._logger.info(
                    "governance.filtered",
                    candidate_id=c.id,
                    decision=decision_str,
                )
                continue

            passed.append(c)

        return passed

    # ── Score Calculation ──────────────────────────────────────────

    def _calculate_score(self, candidate: PlanCandidate) -> float:
        """Calculate a composite score (0.0–1.0) for a candidate.

        Weighted formula:

        - risk_score (lower is better, inverted): 30%
        - confidence (higher is better): 30%
        - historical_success_rate (higher is better): 20%
        - estimated_duration (shorter is better, inverse-log): 10%
        - approval_required (False is better): 10%

        Returns:
            Float score in [0.0, 1.0].
        """
        # 1. Risk contribution (inverted: low risk → high score)
        risk_contrib = (1.0 - candidate.risk_score) * WEIGHT_RISK

        # 2. Confidence contribution
        conf_contrib = candidate.confidence * WEIGHT_CONFIDENCE

        # 3. Historical success contribution
        hist_contrib = candidate.historical_success_rate * WEIGHT_HISTORICAL

        # 4. Duration contribution (inverse-log: shorter → higher score)
        duration_score = self._duration_score(candidate.estimated_duration)
        dur_contrib = duration_score * WEIGHT_DURATION

        # 5. Approval contribution
        approval_score = 1.0 if not candidate.approval_required else 0.0
        appr_contrib = approval_score * WEIGHT_APPROVAL

        # Composite
        score = risk_contrib + conf_contrib + hist_contrib + dur_contrib + appr_contrib

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))

    @staticmethod
    def _duration_score(seconds: int) -> float:
        """Convert estimated duration (seconds) to a score.

        Uses an inverse-log curve so that:
        - 0 seconds → 1.0
        - 60 seconds (1 min) → ~0.76
        - 600 seconds (10 min) → ~0.46
        - 3600 seconds (1 hour) → ~0.21
        """
        if seconds <= 0:
            return 1.0
        return 1.0 / (1.0 + math.log(1.0 + seconds))

    # ── Template Variation Helpers ─────────────────────────────────

    def compute_estimated_duration(self, node_count: int, template_duration: int = 60) -> int:
        """Estimate duration based on node count and base template duration."""
        return template_duration + (node_count * 10)

    def compute_risk_score(
        self,
        has_compensation: bool,
        has_approval_gate: bool,
        base_risk: float = 0.5,
    ) -> float:
        """Compute risk score based on plan features."""
        risk = base_risk
        if has_compensation:
            risk -= 0.1  # Compensation reduces risk
        if has_approval_gate:
            risk -= 0.05  # Approval gate reduces risk
        return max(0.0, min(1.0, risk))
