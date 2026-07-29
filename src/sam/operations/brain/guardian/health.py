"""
OP-322 — Guardian Health Engine

Hitung health score dari:
  - reasoning quality
  - provider availability
  - approval backlog
  - audit consistency
  - trust
  - queue
  - mission load
  - scheduler

Output: HealthScore, HealthIssue, HealthSummary
Rule-based — tidak pakai AI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class HealthIssue:
    component: str
    severity: str  # low, medium, high, critical
    message: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "severity": self.severity,
            "message": self.message,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class HealthScore:
    overall_score: float = 1.0
    reasoning_score: float = 1.0
    provider_score: float = 1.0
    approval_score: float = 1.0
    audit_score: float = 1.0
    trust_score: float = 1.0
    queue_score: float = 1.0
    mission_score: float = 1.0
    scheduler_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 2),
            "reasoning_score": round(self.reasoning_score, 2),
            "provider_score": round(self.provider_score, 2),
            "approval_score": round(self.approval_score, 2),
            "audit_score": round(self.audit_score, 2),
            "trust_score": round(self.trust_score, 2),
            "queue_score": round(self.queue_score, 2),
            "mission_score": round(self.mission_score, 2),
            "scheduler_score": round(self.scheduler_score, 2),
        }


@dataclass(frozen=True)
class HealthSummary:
    status: str  # healthy, degraded, critical
    score: HealthScore
    issues: Tuple[HealthIssue, ...] = ()
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "timestamp": self.timestamp,
        }


class GuardianHealthEngine:
    """
    Rule-based health engine.
    Tidak menggunakan AI — aturan tetap.
    """

    def __init__(self) -> None:
        self._history: List[HealthSummary] = []
        self._max_history: int = 50

    def evaluate(
        self,
        reasoning_ok: bool = True,
        provider_healthy: int = 5,
        provider_degraded: int = 0,
        approval_backlog: int = 0,
        audit_consistent: bool = True,
        trust_level: float = 1.0,
        queue_depth: int = 0,
        mission_active: int = 0,
        mission_capacity: int = 10,
        scheduler_overloaded: bool = False,
        total_reasoning_failures: int = 0,
    ) -> HealthSummary:
        issues: List[HealthIssue] = []

        # Reasoning quality
        reasoning_score = 1.0
        if not reasoning_ok:
            reasoning_score = 0.3
            issues.append(HealthIssue(
                component="reasoning",
                severity="high",
                message="Reasoning quality degraded",
                detail="Reasoning pipeline reported errors",
            ))
        elif total_reasoning_failures > 5:
            reasoning_score = 0.6
            issues.append(HealthIssue(
                component="reasoning",
                severity="medium",
                message="Multiple reasoning failures",
                detail="{} total failures".format(total_reasoning_failures),
            ))

        # Provider availability
        provider_score = 1.0
        total_providers = provider_healthy + provider_degraded
        if total_providers > 0 and provider_degraded > 0:
            ratio = provider_degraded / total_providers
            if ratio > 0.5:
                provider_score = 0.2
                issues.append(HealthIssue(
                    component="provider",
                    severity="critical",
                    message="More than half providers degraded",
                    detail="{}/{} degraded".format(provider_degraded, total_providers),
                ))
            else:
                provider_score = 0.6
                issues.append(HealthIssue(
                    component="provider",
                    severity="medium",
                    message="Some providers degraded",
                    detail="{}/{} degraded".format(provider_degraded, total_providers),
                ))
        if total_providers == 0:
            provider_score = 0.0
            issues.append(HealthIssue(
                component="provider",
                severity="critical",
                message="No providers available",
            ))

        # Approval backlog
        approval_score = 1.0
        if approval_backlog > 20:
            approval_score = 0.3
            issues.append(HealthIssue(
                component="approval",
                severity="high",
                message="Approval backlog critical",
                detail="{} pending approvals".format(approval_backlog),
            ))
        elif approval_backlog > 10:
            approval_score = 0.6
            issues.append(HealthIssue(
                component="approval",
                severity="medium",
                message="Approval backlog growing",
                detail="{} pending approvals".format(approval_backlog),
            ))

        # Audit consistency
        audit_score = 1.0
        if not audit_consistent:
            audit_score = 0.5
            issues.append(HealthIssue(
                component="audit",
                severity="medium",
                message="Audit trail inconsistent",
            ))

        # Trust level
        trust_score = max(0.0, min(1.0, trust_level))
        if trust_score < 0.4:
            issues.append(HealthIssue(
                component="trust",
                severity="high",
                message="Trust level critically low",
                detail="Score: {}".format(round(trust_score, 2)),
            ))
        elif trust_score < 0.7:
            issues.append(HealthIssue(
                component="trust",
                severity="low",
                message="Trust level declining",
                detail="Score: {}".format(round(trust_score, 2)),
            ))

        # Queue
        queue_score = 1.0
        if queue_depth > 50:
            queue_score = 0.3
            issues.append(HealthIssue(
                component="queue",
                severity="high",
                message="Queue depth critical",
                detail="{} items".format(queue_depth),
            ))
        elif queue_depth > 20:
            queue_score = 0.6
            issues.append(HealthIssue(
                component="queue",
                severity="medium",
                message="Queue depth growing",
                detail="{} items".format(queue_depth),
            ))

        # Mission load
        mission_score = 1.0
        if mission_capacity > 0:
            load_ratio = mission_active / mission_capacity
            if load_ratio > 0.9:
                mission_score = 0.3
                issues.append(HealthIssue(
                    component="mission",
                    severity="high",
                    message="Mission load near capacity",
                    detail="{}/{} active".format(mission_active, mission_capacity),
                ))
            elif load_ratio > 0.7:
                mission_score = 0.6
                issues.append(HealthIssue(
                    component="mission",
                    severity="low",
                    message="Mission load elevated",
                    detail="{}/{} active".format(mission_active, mission_capacity),
                ))

        # Scheduler
        scheduler_score = 1.0
        if scheduler_overloaded:
            scheduler_score = 0.3
            issues.append(HealthIssue(
                component="scheduler",
                severity="critical",
                message="Scheduler overloaded",
            ))

        # Overall
        scores = [reasoning_score, provider_score, approval_score,
                  audit_score, trust_score, queue_score, mission_score,
                  scheduler_score]
        overall = sum(scores) / len(scores)

        # Cek komponen terburuk — jika ada yang sangat rendah, status turun
        min_score = min(scores)
        if min_score <= 0.3:
            status = "critical"
        elif min_score <= 0.6 or overall < 0.7:
            status = "degraded"
        else:
            status = "healthy"

        score = HealthScore(
            overall_score=overall,
            reasoning_score=reasoning_score,
            provider_score=provider_score,
            approval_score=approval_score,
            audit_score=audit_score,
            trust_score=trust_score,
            queue_score=queue_score,
            mission_score=mission_score,
            scheduler_score=scheduler_score,
        )

        summary = HealthSummary(
            status=status,
            score=score,
            issues=tuple(issues),
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

        self._history.append(summary)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        return summary

    def latest(self) -> Optional[HealthSummary]:
        if not self._history:
            return None
        return self._history[-1]

    def history(self, limit: int = 10) -> List[HealthSummary]:
        return self._history[-limit:]
