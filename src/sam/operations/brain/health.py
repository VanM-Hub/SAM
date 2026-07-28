"""
OP-257 — Operational Health Engine.

Evaluates health of the entire SAM platform across multiple dimensions.
Produces a score (0–100) and status (GREEN/YELLOW/RED) for each
component and overall platform.

Consumed by: Dashboard, Conversation, Notification, Brain.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class HealthStatus:
    """Health status constants."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

    @staticmethod
    def from_score(score: float) -> str:
        if score >= 80.0:
            return HealthStatus.GREEN
        if score >= 50.0:
            return HealthStatus.YELLOW
        return HealthStatus.RED


@dataclass
class DimensionHealth:
    """Health for a single platform dimension."""

    dimension: str
    score: float  # 0–100
    status: str  # green | yellow | red
    metrics: Dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def __repr__(self) -> str:
        return (
            f"DimensionHealth({self.dimension}: "
            f"{self.score:.0f}/{self.status})"
        )


@dataclass
class OperationalHealthDTO:
    """Complete health snapshot of the platform."""

    timestamp: float
    overall_score: float
    overall_status: str
    dimensions: List[DimensionHealth] = field(default_factory=list)

    @property
    def dimension_map(self) -> Dict[str, DimensionHealth]:
        return {d.dimension: d for d in self.dimensions}

    @property
    def red_dimensions(self) -> List[str]:
        return [d.dimension for d in self.dimensions if d.status == HealthStatus.RED]

    @property
    def yellow_dimensions(self) -> List[str]:
        return [d.dimension for d in self.dimensions if d.status == HealthStatus.YELLOW]

    def get_dimension(self, name: str) -> Optional[DimensionHealth]:
        return self.dimension_map.get(name)

    def __repr__(self) -> str:
        return (
            f"OperationalHealthDTO(overall={self.overall_score:.0f}/"
            f"{self.overall_status}, "
            f"{len(self.dimensions)} dimensions)"
        )


# ── Individual dimension collectors ───────────────────────────────────


def _eval_observation() -> DimensionHealth:
    """Health of observation subsystem."""
    try:
        from sam.operations.brain.observation_engine import ObservationEngine
        engine = ObservationEngine()
        snap = engine.last_snapshot
        if snap is not None:
            return DimensionHealth(
                dimension="observation",
                score=90.0,
                status=HealthStatus.GREEN,
                metrics={"last_snapshot_age": time.time() - snap.timestamp},
                message="Observation engine operational",
            )
        return DimensionHealth(
            dimension="observation",
            score=50.0,
            status=HealthStatus.YELLOW,
            message="No snapshots collected yet",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="observation",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Observation unavailable: {e}",
        )


def _eval_rules() -> DimensionHealth:
    """Health of rule engine."""
    try:
        from sam.operations.brain.rule_engine import RuleEngine
        eng = RuleEngine()
        count = len(eng.rules)
        return DimensionHealth(
            dimension="rules",
            score=85.0,
            status=HealthStatus.GREEN,
            metrics={"rule_count": count},
            message=f"{count} rules registered",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="rules",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Rule engine unavailable: {e}",
        )


def _eval_analyzer() -> DimensionHealth:
    """Health of analyzer."""
    try:
        from sam.operations.brain.analyzer import OperationalAnalyzer
        OperationalAnalyzer()
        return DimensionHealth(
            dimension="analyzer",
            score=90.0,
            status=HealthStatus.GREEN,
            message="Analyzer operational",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="analyzer",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Analyzer unavailable: {e}",
        )


def _eval_learning() -> DimensionHealth:
    """Health of learning subsystem."""
    try:
        from sam.operations.brain.learning_pipeline import LearningPipeline
        pipe = LearningPipeline()
        snapshots = pipe.snapshot_count if hasattr(pipe, 'snapshot_count') else 0
        return DimensionHealth(
            dimension="learning",
            score=80.0,
            status=HealthStatus.GREEN,
            metrics={"snapshots": snapshots},
            message="Learning pipeline operational",
        )
    except Exception:
        return DimensionHealth(
            dimension="learning",
            score=50.0,
            status=HealthStatus.YELLOW,
            message="Learning pipeline not fully initialized",
        )


def _eval_queue() -> DimensionHealth:
    """Health of queue system."""
    try:
        from sam.operations.providers.queue import QueueProvider
        q = QueueProvider()
        size = q.size() if hasattr(q, "size") else 0
        score = 90.0 if size < 50 else (60.0 if size < 200 else 30.0)
        status = HealthStatus.from_score(score)
        return DimensionHealth(
            dimension="queue",
            score=score,
            status=status,
            metrics={"queue_size": size},
            message=f"Queue size: {size}",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="queue",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Queue unavailable: {e}",
        )


def _eval_approval() -> DimensionHealth:
    """Health of approval system."""
    try:
        from sam.operations.approval import get_pending_count
        pending = get_pending_count()
        score = 90.0 if pending < 5 else (60.0 if pending < 20 else 30.0)
        status = HealthStatus.from_score(score)
        return DimensionHealth(
            dimension="approval",
            score=score,
            status=status,
            metrics={"pending_approvals": pending},
            message=f"{pending} pending approvals",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="approval",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Approval unavailable: {e}",
        )


def _eval_trust() -> DimensionHealth:
    """Health of trust system."""
    try:
        from sam.operations.trust import get_trust_summary
        summary = get_trust_summary()
        avg_trust = (
            sum(summary.values()) / len(summary)
            if summary else 1.0
        )
        score = avg_trust * 100.0
        status = HealthStatus.from_score(score)
        return DimensionHealth(
            dimension="trust",
            score=round(score, 1),
            status=status,
            metrics={"avg_trust": round(avg_trust, 2)},
            message=f"Average trust: {avg_trust:.2f}",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="trust",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Trust unavailable: {e}",
        )


def _eval_mission() -> DimensionHealth:
    """Health of mission subsystem."""
    try:
        from sam.operations.mission_query import (
            get_active_missions_count,
            get_failed_missions_count,
        )
        active = get_active_missions_count()
        failed = get_failed_missions_count()
        score = 90.0 if failed == 0 else (60.0 if failed < 3 else 20.0)
        status = HealthStatus.from_score(score)
        return DimensionHealth(
            dimension="mission",
            score=score,
            status=status,
            metrics={"active": active, "failed": failed},
            message=f"{active} active, {failed} failed",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="mission",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Mission unavailable: {e}",
        )


def _eval_storage() -> DimensionHealth:
    """Health of storage subsystem.
    Uses dynamic importlib approach to avoid module-level import side effects.
    """
    import importlib.util
    spec = importlib.util.find_spec("sam.storage")
    if spec is not None:
        try:
            import importlib
            mod = importlib.import_module("sam.storage")
            if hasattr(mod, "get_repository_health"):
                health = mod.get_repository_health()
                all_ok = all(health.values())
                score = 90.0 if all_ok else 50.0
                return DimensionHealth(
                    dimension="storage",
                    score=score,
                    status=HealthStatus.from_score(score),
                    metrics=dict(health),
                    message="All repositories OK" if all_ok else "Some repositories degraded",
                )
        except Exception:
            pass
        return DimensionHealth(
            dimension="storage",
            score=70.0,
            status=HealthStatus.YELLOW,
            message="Storage health check available but failed",
        )
    return DimensionHealth(
        dimension="storage",
        score=50.0,
        status=HealthStatus.YELLOW,
        message="Storage not available",
    )


def _eval_recovery() -> DimensionHealth:
    """Health of recovery subsystem."""
    try:
        from sam.operations.recovery import get_recovery_status
        status = get_recovery_status()
        ok = status.get("enabled", False)
        return DimensionHealth(
            dimension="recovery",
            score=85.0 if ok else 40.0,
            status=HealthStatus.GREEN if ok else HealthStatus.YELLOW,
            metrics=dict(status),
            message="Recovery enabled" if ok else "Recovery not enabled",
        )
    except Exception:
        return DimensionHealth(
            dimension="recovery",
            score=50.0,
            status=HealthStatus.YELLOW,
            message="Recovery status unknown",
        )


def _eval_scheduler() -> DimensionHealth:
    """Health of observation scheduler."""
    try:
        from sam.operations.brain.scheduler import ObservationScheduler
        # Can't check instance state without reference, so check import
        return DimensionHealth(
            dimension="scheduler",
            score=85.0,
            status=HealthStatus.GREEN,
            message="Scheduler module available",
        )
    except Exception:
        return DimensionHealth(
            dimension="scheduler",
            score=0.0,
            status=HealthStatus.RED,
            message="Scheduler unavailable",
        )


def _eval_notification() -> DimensionHealth:
    """Health of notification subsystem."""
    try:
        from sam.operations.notification import get_notification_summary
        summary = get_notification_summary()
        errors = summary.get("error", 0)
        score = 90.0 if errors == 0 else (60.0 if errors < 5 else 30.0)
        return DimensionHealth(
            dimension="notification",
            score=score,
            status=HealthStatus.from_score(score),
            metrics=dict(summary),
            message=f"{errors} error notifications",
        )
    except Exception as e:
        return DimensionHealth(
            dimension="notification",
            score=0.0,
            status=HealthStatus.RED,
            message=f"Notification unavailable: {e}",
        )


# ── All dimension evaluators ──────────────────────────────────────────

_DIMENSIONS: List[str] = [
    "observation",
    "rules",
    "analyzer",
    "learning",
    "queue",
    "approval",
    "trust",
    "mission",
    "storage",
    "recovery",
    "scheduler",
    "notification",
]

_EVALUATORS = {
    "observation": _eval_observation,
    "rules": _eval_rules,
    "analyzer": _eval_analyzer,
    "learning": _eval_learning,
    "queue": _eval_queue,
    "approval": _eval_approval,
    "trust": _eval_trust,
    "mission": _eval_mission,
    "storage": _eval_storage,
    "recovery": _eval_recovery,
    "scheduler": _eval_scheduler,
    "notification": _eval_notification,
}


class OperationalHealthEngine:
    """Evaluates health across all platform dimensions.

    Each dimension produces a score and status.
    Overall score is weighted average of all dimensions.
    """

    def __init__(self) -> None:
        self._last_health: Optional[OperationalHealthDTO] = None

    def evaluate(
        self,
        dimension_names: Optional[List[str]] = None,
    ) -> OperationalHealthDTO:
        """Evaluate health for specified or all dimensions."""
        names = dimension_names or _DIMENSIONS
        dimensions: List[DimensionHealth] = []

        for name in names:
            evaluator = _EVALUATORS.get(name)
            if evaluator is None:
                dimensions.append(DimensionHealth(
                    dimension=name,
                    score=0.0,
                    status=HealthStatus.RED,
                    message=f"Unknown dimension: {name}",
                ))
                continue
            try:
                dimensions.append(evaluator())
            except Exception as e:
                dimensions.append(DimensionHealth(
                    dimension=name,
                    score=0.0,
                    status=HealthStatus.RED,
                    message=str(e),
                ))

        # Overall score = average of all dimension scores
        overall = (
            sum(d.score for d in dimensions) / len(dimensions)
            if dimensions else 0.0
        )

        self._last_health = OperationalHealthDTO(
            timestamp=time.time(),
            overall_score=round(overall, 1),
            overall_status=HealthStatus.from_score(overall),
            dimensions=dimensions,
        )
        return self._last_health

    @property
    def last_health(self) -> Optional[OperationalHealthDTO]:
        return self._last_health

    def evaluate_dimension(self, name: str) -> DimensionHealth:
        """Evaluate a single dimension by name."""
        evaluator = _EVALUATORS.get(name)
        if evaluator is None:
            return DimensionHealth(
                dimension=name,
                score=0.0,
                status=HealthStatus.RED,
                message=f"Unknown dimension: {name}",
            )
        try:
            return evaluator()
        except Exception as e:
            return DimensionHealth(
                dimension=name,
                score=0.0,
                status=HealthStatus.RED,
                message=str(e),
            )


# ── Convenience ───────────────────────────────────────────────────────


def evaluate_health(
    dimension_names: Optional[List[str]] = None,
) -> OperationalHealthDTO:
    """One-shot: evaluate full platform health."""
    return OperationalHealthEngine().evaluate(dimension_names)
