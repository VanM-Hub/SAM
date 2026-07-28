"""
OP-257 — Operational Health Engine.

Computes a composite health score from 8 dimensions:
  Mission, Approval, Trust, Queue, Storage, Recovery, Performance, Audit.

Each dimension produces a 0.0-1.0 score.
Composite = weighted average.
HealthState = healthy (>0.8) | degraded (0.5-0.8) | unhealthy (<0.5).

Output: OperationalHealthDTO
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class DimensionHealth:
    """Health score for a single dimension."""

    dimension: str
    score: float  # 0.0 - 1.0
    status: str  # "healthy" | "degraded" | "unhealthy"
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class OperationalHealthDTO:
    """
    Composite operational health.

    score: 0.0 (dead) to 1.0 (perfect).
    """

    score: float
    status: str  # "healthy" | "degraded" | "unhealthy"
    dimensions: Dict[str, DimensionHealth] = field(default_factory=dict)
    previous_score: Optional[float] = None
    trend: str = "stable"  # "improving" | "declining" | "stable"
    generated_at: float = 0.0

    @property
    def unhealthy_dimensions(self) -> List[str]:
        return [d for d, dh in self.dimensions.items() if dh.status == "unhealthy"]

    @property
    def degraded_dimensions(self) -> List[str]:
        return [d for d, dh in self.dimensions.items() if dh.status == "degraded"]

    @property
    def has_issues(self) -> bool:
        return len(self.unhealthy_dimensions) > 0 or len(self.degraded_dimensions) > 0


# ── Engine ─────────────────────────────────────────────────────────


class OperationalHealthEngine:
    """
    Computes operational health from a MultiSourceSnapshot.

    Each dimension uses specific fields from the snapshot.
    """

    def __init__(self):
        self._last_health: Optional[OperationalHealthDTO] = None

    # ── Public API ─────────────────────────────────────────────────

    @property
    def last_health(self) -> Optional[OperationalHealthDTO]:
        return self._last_health

    def evaluate(
        self,
        source_data: Dict[str, Dict[str, Any]],
        previous_score: Optional[float] = None,
    ) -> OperationalHealthDTO:
        """
        Evaluate health from source data dict.

        source_data keys: missions, approvals, timeline, trust,
                          scheduler, notification, locks, health, etc.
        """
        dimensions: Dict[str, DimensionHealth] = {}

        # Compute each dimension
        dimensions["mission"] = self._mission_health(
            source_data.get("missions", {}))
        dimensions["approval"] = self._approval_health(
            source_data.get("approvals", {}))
        dimensions["trust"] = self._trust_health(
            source_data.get("trust", {}))
        dimensions["queue"] = self._queue_health(
            source_data.get("scheduler", {}))
        dimensions["storage"] = self._storage_health(
            source_data.get("health", source_data.get("missions", {})))
        dimensions["recovery"] = self._recovery_health(
            source_data.get("replay", {}))
        dimensions["performance"] = self._performance_health(
            source_data.get("benchmark", {}))
        dimensions["audit"] = self._audit_health(
            source_data.get("audit", {}))

        # Weighted composite (all equal by default)
        scores = [d.score for d in dimensions.values()]
        composite = sum(scores) / len(scores) if scores else 1.0
        status = self._status_from_score(composite)

        # Trend
        trend = self._compute_trend(composite, previous_score)

        health = OperationalHealthDTO(
            score=round(composite, 4),
            status=status,
            dimensions=dimensions,
            previous_score=previous_score,
            trend=trend,
            generated_at=__import__("time").time(),
        )
        self._last_health = health
        return health

    # ── Dimension evaluators ───────────────────────────────────────

    def _mission_health(self, data: Dict[str, Any]) -> DimensionHealth:
        active = data.get("active", 0)
        failed = data.get("failed", 0)
        total = data.get("total", 0) or 1
        failure_rate = failed / total
        score = max(0.0, 1.0 - failure_rate * 2 - active * 0.02)
        score = min(1.0, score)
        return DimensionHealth(
            dimension="mission", score=round(score, 4),
            status=self._status_from_score(score),
            details={"active": active, "failed": failed, "total": total},
            warnings=[f"{failed} failed missions"] if failed > 2 else [],
            errors=[f"High failure rate: {failure_rate:.0%}"] if failure_rate > 0.3 else [],
        )

    def _approval_health(self, data: Dict[str, Any]) -> DimensionHealth:
        pending = data.get("pending", 0)
        total = data.get("total", 0) or 1
        score = max(0.0, 1.0 - pending * 0.1)
        return DimensionHealth(
            dimension="approval", score=round(score, 4),
            status=self._status_from_score(score),
            details={"pending": pending, "total": total},
            warnings=[f"{pending} pending approvals"] if pending > 5 else [],
            errors=[] if pending < 15 else [f"Approval backlog: {pending}"],
        )

    def _trust_health(self, data: Dict[str, Any]) -> DimensionHealth:
        overall = data.get("overall", 1.0)
        below = data.get("components_below_threshold", 0)
        score = max(0.0, min(1.0, overall - below * 0.15))
        return DimensionHealth(
            dimension="trust", score=round(score, 4),
            status=self._status_from_score(score),
            details={"overall": overall, "below_threshold": below},
            warnings=[f"Trust components below threshold: {below}"] if below > 0 else [],
            errors=[f"Trust critically low: {overall:.2f}"] if overall < 0.4 else [],
        )

    def _queue_health(self, data: Dict[str, Any]) -> DimensionHealth:
        queue_len = data.get("queue_length", 0)
        stalled = data.get("stalled", 0)
        score = max(0.0, 1.0 - queue_len * 0.02 - stalled * 0.25)
        return DimensionHealth(
            dimension="queue", score=round(score, 4),
            status=self._status_from_score(score),
            details={"queue_length": queue_len, "stalled": stalled},
            warnings=[f"Queue length: {queue_len}"] if queue_len > 20 else [],
            errors=[f"Stalled items: {stalled}"] if stalled > 0 else [],
        )

    def _storage_health(self, data: Dict[str, Any]) -> DimensionHealth:
        downtime = data.get("downtime_seconds", 0)
        score = max(0.0, 1.0 - downtime / 3600.0)
        return DimensionHealth(
            dimension="storage", score=round(score, 4),
            status=self._status_from_score(score),
            details={"downtime_seconds": downtime},
            errors=[f"Downtime: {downtime}s"] if downtime > 60 else [],
        )

    def _recovery_health(self, data: Dict[str, Any]) -> DimensionHealth:
        success_rate = data.get("success_rate", 1.0)
        failed = data.get("failed", 0)
        score = max(0.0, min(1.0, success_rate - failed * 0.1))
        return DimensionHealth(
            dimension="recovery", score=round(score, 4),
            status=self._status_from_score(score),
            details={"success_rate": success_rate, "failed": failed},
            warnings=[f"Replay failures: {failed}"] if failed > 0 else [],
            errors=[f"Recovery success rate low: {success_rate:.0%}"] if success_rate < 0.7 else [],
        )

    def _performance_health(self, data: Dict[str, Any]) -> DimensionHealth:
        error_rate = data.get("error_rate", 0.0)
        score = max(0.0, 1.0 - error_rate * 2)
        return DimensionHealth(
            dimension="performance", score=round(score, 4),
            status=self._status_from_score(score),
            details=dict(data),
            errors=[f"Error rate: {error_rate:.1%}"] if error_rate > 0.1 else [],
        )

    def _audit_health(self, data: Dict[str, Any]) -> DimensionHealth:
        overridden = data.get("overridden", 0)
        total = data.get("total_decisions", 0) or 1
        override_rate = overridden / total
        score = max(0.0, 1.0 - override_rate * 3)
        return DimensionHealth(
            dimension="audit", score=round(score, 4),
            status=self._status_from_score(score),
            details={"total_decisions": total, "overridden": overridden},
            warnings=[f"Overrides: {overridden}"] if overridden > 0 else [],
            errors=[f"High override rate: {override_rate:.0%}"] if override_rate > 0.2 else [],
        )

    # ── Helpers ────────────────────────────────────────────────────

    def _status_from_score(self, score: float) -> str:
        if score >= 0.8:
            return "healthy"
        elif score >= 0.5:
            return "degraded"
        return "unhealthy"

    def _compute_trend(self, current: float, previous: Optional[float]) -> str:
        if previous is None:
            return "stable"
        diff = current - previous
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"


# ── Convenience ────────────────────────────────────────────────────


def evaluate_health(
    source_data: Dict[str, Dict[str, Any]],
    previous_score: Optional[float] = None,
) -> OperationalHealthDTO:
    """One-shot: evaluate operational health."""
    engine = OperationalHealthEngine()
    return engine.evaluate(source_data, previous_score)
