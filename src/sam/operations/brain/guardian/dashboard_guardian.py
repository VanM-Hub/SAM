"""
OP-327 — Guardian Dashboard (Supervisory)

DTO:
  - GuardianSupervisoryDashboard
  - GuardianSupervisoryPanel
  - GuardianSupervisoryMetric
  - GuardianSupervisoryIssue
  - GuardianSupervisoryRecommendation
  - GuardianSupervisoryStatusCard

Tidak ada UI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianSupervisoryMetric:
    name: str
    value: float
    unit: str = ""
    trend: str = "stable"  # up, down, stable
    threshold: Optional[float] = None
    healthy: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "trend": self.trend,
            "threshold": self.threshold,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class GuardianSupervisoryIssue:
    component: str
    severity: str
    message: str
    detail: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "severity": self.severity,
            "message": self.message,
            "detail": self.detail,
            "source": self.source,
        }


@dataclass(frozen=True)
class GuardianSupervisoryRecommendation:
    recommendation_type: str
    priority: str
    title: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_type": self.recommendation_type,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
        }


@dataclass(frozen=True)
class GuardianSupervisoryStatusCard:
    title: str
    status: str  # healthy, degraded, critical, unknown
    value: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "status": self.status,
            "value": self.value,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GuardianSupervisoryPanel:
    title: str
    metrics: Tuple[GuardianSupervisoryMetric, ...] = ()
    issues: Tuple[GuardianSupervisoryIssue, ...] = ()
    recommendations: Tuple[GuardianSupervisoryRecommendation, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "metrics": [m.to_dict() for m in self.metrics],
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


@dataclass(frozen=True)
class GuardianSupervisoryDashboard:
    status_cards: Tuple[GuardianSupervisoryStatusCard, ...] = ()
    panels: Tuple[GuardianSupervisoryPanel, ...] = ()
    overall_status: str = "unknown"
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "last_updated": self.last_updated,
            "status_cards": [s.to_dict() for s in self.status_cards],
            "panels": [p.to_dict() for p in self.panels],
        }


class GuardianSupervisoryDashboardService:
    """
    Dashboard read-only untuk Guardian Supervisor.
    Tidak membuat UI — hanya menyusun DTO.
    """

    def __init__(
        self,
        health_engine: Any,
        supervisor: Any,
        watchdog: Any,
        policy_evaluator: Any,
        recommendation_engine: Any,
        conversation: Any,
    ) -> None:
        self._health = health_engine
        self._supervisor = supervisor
        self._watchdog = watchdog
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._conversation = conversation

    def get_dashboard(self) -> GuardianSupervisoryDashboard:
        now = datetime.now().isoformat(timespec="seconds")
        health = self._health.latest()
        snapshot = self._supervisor.latest()

        # Status cards
        health_status = health.status if health else "unknown"
        cards = (
            GuardianSupervisoryStatusCard(
                title="Guardian Health",
                status=health_status,
                value=health.status.upper() if health else "UNKNOWN",
                detail="Score: {:.2f}".format(health.score.overall_score) if health else "",
            ),
            GuardianSupervisoryStatusCard(
                title="Supervisor",
                status="issues" if (snapshot and self._supervisor.has_overall_issues) else "healthy",
                value="Has Issues" if (snapshot and self._supervisor.has_overall_issues) else "Healthy",
            ),
            GuardianSupervisoryStatusCard(
                title="Policy Compliance",
                status="passed" if self._policy.all_passed else "violations",
                value="{} / 8".format(sum(1 for r in self._policy.results if r.passed)),
                detail="{} violations".format(len(self._policy.violations)),
            ),
            GuardianSupervisoryStatusCard(
                title="Recommendations",
                status="action" if len(self._recommendation.recommendations) > 0 else "none",
                value=str(len(self._recommendation.recommendations)),
            ),
        )

        # Panels
        panels: List[GuardianSupervisoryPanel] = []

        # Health panel
        health_metrics: List[GuardianSupervisoryMetric] = []
        health_issues: List[GuardianSupervisoryIssue] = []
        if health:
            health_metrics = [
                GuardianSupervisoryMetric(name="Overall", value=round(health.score.overall_score, 2),
                                          threshold=0.7, healthy=health.score.overall_score >= 0.7),
                GuardianSupervisoryMetric(name="Reasoning", value=round(health.score.reasoning_score, 2)),
                GuardianSupervisoryMetric(name="Provider", value=round(health.score.provider_score, 2)),
                GuardianSupervisoryMetric(name="Approval", value=round(health.score.approval_score, 2)),
                GuardianSupervisoryMetric(name="Mission", value=round(health.score.mission_score, 2)),
                GuardianSupervisoryMetric(name="Scheduler", value=round(health.score.scheduler_score, 2)),
            ]
            for i in health.issues:
                health_issues.append(GuardianSupervisoryIssue(
                    component=i.component, severity=i.severity,
                    message=i.message, detail=i.detail, source="health",
                ))
        panels.append(GuardianSupervisoryPanel(
            title="Health",
            metrics=tuple(health_metrics),
            issues=tuple(health_issues),
        ))

        # Policy panel
        policy_metrics: List[GuardianSupervisoryMetric] = []
        policy_issues: List[GuardianSupervisoryIssue] = []
        for r in self._policy.results:
            policy_metrics.append(GuardianSupervisoryMetric(
                name=r.policy, value=r.score, healthy=r.passed,
            ))
            for v in r.violations:
                policy_issues.append(GuardianSupervisoryIssue(
                    component=v.policy, severity=v.severity,
                    message=v.message, detail=v.detail, source="policy",
                ))
        panels.append(GuardianSupervisoryPanel(
            title="Policy",
            metrics=tuple(policy_metrics),
            issues=tuple(policy_issues),
        ))

        # Watchdog panel
        wd_issues: List[GuardianSupervisoryIssue] = []
        for a in self._watchdog.alerts:
            wd_issues.append(GuardianSupervisoryIssue(
                component=a.component, severity=a.severity,
                message=a.message, detail=a.detail, source="watchdog",
            ))
        for i in self._watchdog.incidents:
            wd_issues.append(GuardianSupervisoryIssue(
                component=i.component, severity=i.severity,
                message=i.message, detail=i.detail, source="incident",
            ))
        panels.append(GuardianSupervisoryPanel(
            title="Watchdog",
            issues=tuple(wd_issues),
        ))

        # Recommendations panel
        panel_recs: List[GuardianSupervisoryRecommendation] = []
        for r in self._recommendation.recommendations:
            panel_recs.append(GuardianSupervisoryRecommendation(
                recommendation_type=r.recommendation_type,
                priority=r.priority, title=r.title, description=r.description,
            ))
        panels.append(GuardianSupervisoryPanel(
            title="Recommendations",
            recommendations=tuple(panel_recs),
        ))

        # Supervisor panel
        sup_metrics: List[GuardianSupervisoryMetric] = []
        if snapshot:
            sup_metrics = [
                GuardianSupervisoryMetric(name="Reasoning Sessions", value=snapshot.reasoning.active_sessions, unit="sessions"),
                GuardianSupervisoryMetric(name="Active Missions", value=snapshot.mission.active_missions, unit="missions"),
                GuardianSupervisoryMetric(name="Pending Approvals", value=snapshot.decision.pending_approvals, unit="approvals"),
                GuardianSupervisoryMetric(name="Queue Depth", value=snapshot.scheduler.tasks_queued, unit="tasks"),
            ]
        panels.append(GuardianSupervisoryPanel(
            title="Supervisor",
            metrics=tuple(sup_metrics),
        ))

        overall = "healthy"
        if any(s.status == "issues" for s in cards):
            overall = "degraded"
        if any(s.status == "violations" for s in cards):
            overall = "critical"
        if health_status == "critical":
            overall = "critical"

        return GuardianSupervisoryDashboard(
            status_cards=tuple(cards),
            panels=tuple(panels),
            overall_status=overall,
            last_updated=now,
        )
