"""
OP-263 — Optimizer.

Jika rekomendasi lama gagal → turunkan confidence.
Jika berhasil → naikkan confidence.

All deterministic, no ML/AI.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class OptimizerResult:
    """Result of optimizing a recommendation."""
    recommendation_id: str
    original_confidence: float
    adjusted_confidence: float
    change_amount: float
    direction: str  # "increase" | "decrease" | "unchanged"
    reason: str
    history_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    optimized_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "original_confidence": self.original_confidence,
            "adjusted_confidence": self.adjusted_confidence,
            "change": f"{self.direction} by {abs(self.change_amount):.4f}",
            "reason": self.reason,
        }


@dataclass
class OptimizationReport:
    """Report of all optimizations in a session."""
    results: List[OptimizerResult] = field(default_factory=list)
    total_adjusted: int = 0
    total_increased: int = 0
    total_decreased: int = 0
    avg_change: float = 0.0
    generated_at: float = 0.0


@dataclass
class OptimizerConfig:
    """Configuration for recommendation optimizer."""
    success_boost: float = 0.05      # Increase when successful
    failure_penalty: float = 0.10    # Decrease when failed
    max_confidence: float = 0.99
    min_confidence: float = 0.05
    min_records_buffer: int = 3      # Minimum records before adjusting
    consecutive_success_bonus: float = 0.03
    consecutive_failure_multiplier: float = 1.5
    history_window_hours: float = 168.0  # 7 days default


# ── Engine ─────────────────────────────────────────────────────────


class RecommendationOptimizer:
    """
    Adjust confidence of recommendations based on outcomes.

    Rules:
      - If outcome is success: boost confidence
      - If outcome is failure: reduce confidence
      - Consecutive successes → extra boost
      - Consecutive failures → extra penalty
      - Final confidence clamped to [min_confidence, max_confidence]
    """

    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self._outcomes: Dict[str, List[bool]] = {}
        self._last_report: Optional[OptimizationReport] = None

    @property
    def last_report(self) -> Optional[OptimizationReport]:
        return self._last_report

    def record_outcome(self, recommendation_id: str, success: bool) -> None:
        """Record an outcome for learning."""
        if recommendation_id not in self._outcomes:
            self._outcomes[recommendation_id] = []
        self._outcomes[recommendation_id].append(success)

    def record_outcomes(self, outcomes: Dict[str, List[bool]]) -> None:
        """Bulk record outcomes."""
        for rec_id, outcomes_list in outcomes.items():
            if rec_id not in self._outcomes:
                self._outcomes[rec_id] = []
            self._outcomes[rec_id].extend(outcomes_list)

    def optimize(
        self,
        recommendation_id: str,
        current_confidence: float,
    ) -> OptimizerResult:
        """
        Optimize confidence based on recorded outcome history.

        Args:
          recommendation_id: The recommendation to optimize
          current_confidence: Current confidence value (0.0-1.0)

        Returns: OptimizerResult with adjusted confidence
        """
        outcomes = self._outcomes.get(recommendation_id, [])
        adjusted = self._adjust_confidence(current_confidence, outcomes)

        direction = "unchanged"
        if adjusted > current_confidence:
            direction = "increase"
        elif adjusted < current_confidence:
            direction = "decrease"

        result = OptimizerResult(
            recommendation_id=recommendation_id,
            original_confidence=current_confidence,
            adjusted_confidence=adjusted,
            change_amount=adjusted - current_confidence,
            direction=direction,
            reason=self._build_reason(adjusted, current_confidence, outcomes),
            history_count=len(outcomes),
            success_count=sum(1 for o in outcomes if o),
            failure_count=sum(1 for o in outcomes if not o),
            optimized_at=time.time(),
        )
        return result

    def optimize_batch(
        self,
        recommendations: Dict[str, float],
    ) -> OptimizationReport:
        """
        Optimize multiple recommendations at once.

        Args:
          recommendations: Dict of {rec_id: current_confidence}

        Returns: OptimizationReport
        """
        results = []
        for rec_id, confidence in recommendations.items():
            results.append(self.optimize(rec_id, confidence))

        increases = [r for r in results if r.direction == "increase"]
        decreases = [r for r in results if r.direction == "decrease"]
        changes = [abs(r.change_amount) for r in results]

        report = OptimizationReport(
            results=results,
            total_adjusted=len(increases) + len(decreases),
            total_increased=len(increases),
            total_decreased=len(decreases),
            avg_change=sum(changes) / len(changes) if changes else 0.0,
            generated_at=time.time(),
        )
        self._last_report = report
        return report

    def get_outcome_history(self, recommendation_id: str) -> List[bool]:
        """Get outcome history for a recommendation."""
        return list(self._outcomes.get(recommendation_id, []))

    def get_success_rate(self, recommendation_id: str) -> float:
        """Get success rate from history."""
        outcomes = self._outcomes.get(recommendation_id, [])
        if not outcomes:
            return 0.0
        return sum(1 for o in outcomes if o) / len(outcomes)

    def clear(self, recommendation_id: Optional[str] = None) -> None:
        """Clear outcome history."""
        if recommendation_id:
            self._outcomes.pop(recommendation_id, None)
        else:
            self._outcomes.clear()

    # ── Internal ───────────────────────────────────────────────────

    def _adjust_confidence(
        self, current: float, outcomes: List[bool]
    ) -> float:
        c = self.config
        if len(outcomes) < c.min_records_buffer:
            return current

        adjusted = current
        # Recent outcomes matter more: weight last 5
        recent = outcomes[-10:]
        success_count = sum(1 for o in recent if o)
        failure_count = sum(1 for o in recent if not o)

        # Net adjustment from individual outcomes
        adjusted += success_count * c.success_boost
        adjusted -= failure_count * c.failure_penalty

        # Consecutive bonus/penalty
        consecutive_successes = self._count_consecutive(recent, True)
        consecutive_failures = self._count_consecutive(recent, False)

        if consecutive_successes >= 3:
            adjusted += c.consecutive_success_bonus * (consecutive_successes - 2)
        if consecutive_failures >= 2:
            adjusted -= (
                c.failure_penalty * c.consecutive_failure_multiplier *
                (consecutive_failures - 1)
            )

        return max(c.min_confidence, min(c.max_confidence, adjusted))

    def _count_consecutive(
        self, outcomes: List[bool], value: bool
    ) -> int:
        """Count trailing consecutive outcomes matching value."""
        count = 0
        for o in reversed(outcomes):
            if o == value:
                count += 1
            else:
                break
        return count

    def _build_reason(
        self,
        adjusted: float,
        original: float,
        outcomes: List[bool],
    ) -> str:
        if not outcomes:
            return "No outcome data yet"
        successes = sum(1 for o in outcomes if o)
        failures = sum(1 for o in outcomes if not o)
        changes = []
        if successes >= 3:
            changes.append(f"+{successes * 0.05:.2f} from successes")
        if failures >= 1:
            changes.append(f"-{failures * 0.10:.2f} from failures")
        return f"Successes: {successes}, Failures: {failures} → {changes}"

    def __len__(self) -> int:
        return len(self._outcomes)


# ── Convenience ────────────────────────────────────────────────────


def optimize_recommendation(
    recommendation_id: str,
    current_confidence: float,
    outcomes: Optional[List[bool]] = None,
    config: Optional[OptimizerConfig] = None,
) -> OptimizerResult:
    """One-shot: optimize recommendation confidence."""
    optimizer = RecommendationOptimizer(config)
    if outcomes:
        optimizer.record_outcome(recommendation_id, outcomes)
    return optimizer.optimize(recommendation_id, current_confidence)


def adjust_recommendations(
    confidences: Dict[str, float],
    outcomes: Dict[str, List[bool]],
) -> OptimizationReport:
    """One-shot: optimize multiple recommendations."""
    optimizer = RecommendationOptimizer()
    optimizer.record_outcomes(outcomes)
    return optimizer.optimize_batch(confidences)
