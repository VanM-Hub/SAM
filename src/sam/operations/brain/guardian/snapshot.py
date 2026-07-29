"""
OP-332 — Guardian Snapshot Engine

Mengumpulkan state sistem menjadi satu snapshot immutable.
Digunakan oleh dashboard, conversation, dan history.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardianMetrics:
    """Metrics snapshot — angka-angka performa."""
    reasoning_sessions: int = 0
    reasoning_failures: int = 0
    reasoning_completed: int = 0
    active_mission_count: int = 0
    stalled_mission_count: int = 0
    pending_approval_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    provider_healthy: int = 0
    provider_degraded: int = 0
    provider_unhealthy: int = 0
    queue_depth: int = 0
    tasks_queued: int = 0
    tasks_completed: int = 0
    retry_count: int = 0
    failure_count: int = 0
    policy_violation_count: int = 0
    watchdog_alert_count: int = 0
    watchdog_warning_count: int = 0
    recommendation_count: int = 0
    trust_level: float = 1.0
    audit_consistency: float = 1.0
    scheduler_score: float = 1.0


@dataclass(frozen=True)
class GuardianSection:
    """Satu section dari snapshot — menyimpan state terstruktur."""
    name: str
    status: str = "unknown"
    score: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    issues: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GuardianHealthSnapshot:
    """Ringkasan kesehatan dalam snapshot."""
    status: str = "unknown"
    overall_score: float = 0.0
    sections: Tuple[GuardianSection, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GuardianSnapshot:
    """Snapshot lengkap — immutable, semua state pipeline."""
    timestamp: str = ""
    pipeline_stage: str = "idle"
    health: GuardianHealthSnapshot = field(default_factory=GuardianHealthSnapshot)
    metrics: GuardianMetrics = field(default_factory=GuardianMetrics)
    errors: Tuple[str, ...] = field(default_factory=tuple)
    system_status: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "pipeline_stage": self.pipeline_stage,
            "system_status": self.system_status,
            "health": {
                "status": self.health.status,
                "overall_score": self.health.overall_score,
                "sections": [
                    {
                        "name": s.name, "status": s.status,
                        "score": s.score, "issues": list(s.issues),
                    }
                    for s in self.health.sections
                ],
            },
            "metrics": {
                "reasoning_sessions": self.metrics.reasoning_sessions,
                "pending_approvals": self.metrics.pending_approval_count,
                "provider_healthy": self.metrics.provider_healthy,
                "queue_depth": self.metrics.queue_depth,
                "policy_violations": self.metrics.policy_violation_count,
                "recommendations": self.metrics.recommendation_count,
            },
            "errors": list(self.errors),
        }


# ══════════════════════════════════════════════════════════════════════
# Snapshot Engine
# ══════════════════════════════════════════════════════════════════════

class GuardianSnapshotEngine:
    """Mengumpulkan state dari engine terdaftar menjadi satu snapshot."""

    def __init__(
        self,
        health_engine: Any = None,
        supervisor: Any = None,
        watchdog: Any = None,
        policy_evaluator: Any = None,
        recommendation_engine: Any = None,
    ):
        self._health = health_engine
        self._supervisor = supervisor
        self._watchdog = watchdog
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._snapshots: List[GuardianSnapshot] = []

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def last_snapshot(self) -> Optional[GuardianSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def collect(self, **kw: Any) -> GuardianSnapshot:
        """Kumpulkan snapshot dari semua engine terdaftar."""
        now = datetime.now().isoformat(timespec="seconds")
        errors: List[str] = []

        # Health
        health = None
        if self._health:
            try:
                health = self._health.latest()
            except Exception:
                pass

        # Supervisor snapshot
        supervisor_snap = None
        if self._supervisor:
            try:
                supervisor_snap = self._supervisor.latest()
            except Exception:
                pass

        # Buat sections dari health & supervisor
        sections: List[GuardianSection] = []

        if health:
            sections.append(GuardianSection(
                name="overall",
                status=health.status,
                score=health.score.overall_score,
                issues=tuple(i.message for i in health.issues),
            ))
        else:
            sections.append(GuardianSection(name="overall", status="unchecked"))

        if supervisor_snap:
            sections.append(GuardianSection(
                name="supervisor",
                status="issues" if supervisor_snap.reasoning.active_sessions > 0 and supervisor_snap.reasoning.failed_count > 0 else "stable",
                score=1.0 - (supervisor_snap.reasoning.failed_count / max(
                    supervisor_snap.reasoning.active_sessions, 1)) * 0.1,
            ))

        health_snap = GuardianHealthSnapshot(
            status=health.status if health else "unchecked",
            overall_score=health.score.overall_score if health else 0.0,
            sections=tuple(sections),
        )

        # Metrics
        provisioned = kw.get("provider_healthy", 0) + kw.get("provider_degraded", 0)
        metrics = GuardianMetrics(
            reasoning_sessions=kw.get("reasoning_sessions",
                supervisor_snap.reasoning.active_sessions if supervisor_snap else 0),
            reasoning_failures=kw.get("failure_count",
                supervisor_snap.reasoning.failed_count if supervisor_snap else 0),
            pending_approval_count=kw.get("pending_approvals", 0),
            provider_healthy=kw.get("provider_healthy", provisioned),
            provider_degraded=kw.get("provider_degraded", 0),
            queue_depth=kw.get("queue_depth", 0),
            policy_violation_count=len(self._policy.violations) if self._policy else 0,
            watchdog_alert_count=len(self._watchdog.alerts) if self._watchdog else 0,
            watchdog_warning_count=len(self._watchdog.warnings) if self._watchdog else 0,
            recommendation_count=len(self._recommendation.recommendations) if self._recommendation else 0,
        )

        system_status = "healthy"
        if errors:
            system_status = "error"
        elif health and health.status == "critical":
            system_status = "critical"
        elif health and health.status == "degraded":
            system_status = "degraded"

        snap = GuardianSnapshot(
            timestamp=now,
            pipeline_stage=kw.get("pipeline_stage", "idle"),
            health=health_snap,
            metrics=metrics,
            errors=tuple(errors),
            system_status=system_status,
        )

        self._snapshots.append(snap)
        return snap

    def clear(self) -> None:
        self._snapshots.clear()
