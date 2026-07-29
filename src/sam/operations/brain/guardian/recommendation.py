"""
OP-325 — Guardian Recommendation Engine

Mengubah Health, Policy, Watchdog, Reasoning menjadi GuardianRecommendation.
Contoh: Pause Scheduler, Request Approval, Rotate Provider, Retry Later,
         Reduce Load, Investigate Queue, Checkpoint Mission.

Tidak boleh mengeksekusi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianRecommendation:
    recommendation_type: str
    priority: str  # low, medium, high, critical
    source: str  # health, policy, watchdog, reasoning
    title: str
    description: str = ""
    evidence: Tuple[str, ...] = ()
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_type": self.recommendation_type,
            "priority": self.priority,
            "source": self.source,
            "title": self.title,
            "description": self.description,
            "evidence": list(self.evidence),
            "timestamp": self.timestamp,
        }


class GuardianRecommendationEngine:
    """
    Recommendation engine — evidence-based, read-only.
    """

    def __init__(self) -> None:
        self._recommendations: List[GuardianRecommendation] = []
        self._max_recommendations: int = 100

    # ── From Health ────────────────────────────────────────────────────

    def from_health(self, health_status: str, health_score: float,
                    issues: Tuple[Any, ...]) -> List[GuardianRecommendation]:
        recs: List[GuardianRecommendation] = []
        now = datetime.now().isoformat(timespec="seconds")

        if health_status == "critical":
            recs.append(GuardianRecommendation(
                recommendation_type="pause_scheduler",
                priority="critical",
                source="health",
                title="Pause Scheduler",
                description="Health status is critical. Pause scheduler to prevent further degradation.",
                evidence=("Health score: {:.2f}".format(health_score),),
                timestamp=now,
            ))

        if health_score < 0.5:
            recs.append(GuardianRecommendation(
                recommendation_type="reduce_load",
                priority="high",
                source="health",
                title="Reduce Load",
                description="Reduce system load to recover health score.",
                evidence=("Health score: {:.2f}".format(health_score),),
                timestamp=now,
            ))

        for issue in issues:
            if hasattr(issue, "component") and issue.component == "provider":
                recs.append(GuardianRecommendation(
                    recommendation_type="rotate_provider",
                    priority="medium",
                    source="health",
                    title="Rotate Provider",
                    description="Provider health issue detected.",
                    evidence=(issue.message,),
                    timestamp=now,
                ))

        return recs

    # ── From Policy ────────────────────────────────────────────────────

    def from_policy(self, policy_violations: Tuple[Any, ...]) -> List[GuardianRecommendation]:
        recs: List[GuardianRecommendation] = []
        now = datetime.now().isoformat(timespec="seconds")

        for v in policy_violations:
            if v.policy == "ApprovalRequired":
                recs.append(GuardianRecommendation(
                    recommendation_type="request_approval",
                    priority="high" if v.severity == "high" else "medium",
                    source="policy",
                    title="Request Approval",
                    description="Approval policy violated.",
                    evidence=(v.message, v.detail),
                    timestamp=now,
                ))
            elif v.policy == "ProviderHealthy":
                recs.append(GuardianRecommendation(
                    recommendation_type="retry_later",
                    priority="medium",
                    source="policy",
                    title="Retry Later",
                    description="Provider health policy violated. Retry when providers recover.",
                    evidence=(v.message, v.detail),
                    timestamp=now,
                ))

        return recs

    # ── From Watchdog ──────────────────────────────────────────────────

    def from_watchdog(
        self,
        alerts: Tuple[Any, ...],
        warnings: Tuple[Any, ...],
        incidents: Tuple[Any, ...],
    ) -> List[GuardianRecommendation]:
        recs: List[GuardianRecommendation] = []
        now = datetime.now().isoformat(timespec="seconds")

        for alert in alerts:
            if hasattr(alert, "alert_type"):
                if "stuck" in alert.alert_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="investigate_queue",
                        priority="high",
                        source="watchdog",
                        title="Investigate Queue",
                        description="Stuck reasoning detected. Investigate queue.",
                        evidence=(alert.message, alert.detail),
                        timestamp=now,
                    ))
                elif "deadlock" in alert.alert_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="request_approval",
                        priority="critical",
                        source="watchdog",
                        title="Request Approval",
                        description="Approval deadlock detected.",
                        evidence=(alert.message,),
                        timestamp=now,
                    ))
                elif "overload" in alert.alert_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="reduce_load",
                        priority="high",
                        source="watchdog",
                        title="Reduce Load",
                        description="Scheduler overload detected.",
                        evidence=(alert.message,),
                        timestamp=now,
                    ))

        for warning in warnings:
            if hasattr(warning, "warning_type"):
                if "provider" in warning.warning_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="rotate_provider",
                        priority="medium",
                        source="watchdog",
                        title="Rotate Provider",
                        description=warning.message,
                        evidence=(warning.detail,),
                        timestamp=now,
                    ))
                elif "retry" in warning.warning_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="checkpoint_mission",
                        priority="medium",
                        source="watchdog",
                        title="Checkpoint Mission",
                        description="Excessive retries detected. Consider checkpoint.",
                        evidence=(warning.message,),
                        timestamp=now,
                    ))
                elif "queue" in warning.warning_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="investigate_queue",
                        priority="medium",
                        source="watchdog",
                        title="Investigate Queue",
                        description=warning.message,
                        evidence=(warning.detail,),
                        timestamp=now,
                    ))

        for incident in incidents:
            if hasattr(incident, "incident_type"):
                if "failure" in incident.incident_type:
                    recs.append(GuardianRecommendation(
                        recommendation_type="investigate_queue",
                        priority="high",
                        source="watchdog",
                        title="Investigate Queue",
                        description="Repeated failures detected.",
                        evidence=(incident.message,),
                        timestamp=now,
                    ))

        return recs

    # ── From Reasoning ─────────────────────────────────────────────────

    def from_reasoning(
        self,
        reasoning_failures: int = 0,
        active_sessions: int = 0,
    ) -> List[GuardianRecommendation]:
        recs: List[GuardianRecommendation] = []
        now = datetime.now().isoformat(timespec="seconds")

        if reasoning_failures > 5:
            recs.append(GuardianRecommendation(
                recommendation_type="retry_later",
                priority="medium",
                source="reasoning",
                title="Retry Later",
                description="Multiple reasoning failures. Retry after investigation.",
                evidence=("{} failures".format(reasoning_failures),),
                timestamp=now,
            ))

        if active_sessions > 10:
            recs.append(GuardianRecommendation(
                recommendation_type="reduce_load",
                priority="low",
                source="reasoning",
                title="Reduce Load",
                description="High number of active reasoning sessions.",
                evidence=("{} active".format(active_sessions),),
                timestamp=now,
            ))

        return recs

    # ── Aggregate ──────────────────────────────────────────────────────

    def aggregate(
        self,
        health_status: str = "healthy",
        health_score: float = 1.0,
        health_issues: Tuple[Any, ...] = (),
        policy_violations: Tuple[Any, ...] = (),
        watchdog_alerts: Tuple[Any, ...] = (),
        watchdog_warnings: Tuple[Any, ...] = (),
        watchdog_incidents: Tuple[Any, ...] = (),
        reasoning_failures: int = 0,
        active_sessions: int = 0,
    ) -> List[GuardianRecommendation]:
        recs: List[GuardianRecommendation] = []
        recs.extend(self.from_health(health_status, health_score, health_issues))
        recs.extend(self.from_policy(policy_violations))
        recs.extend(self.from_watchdog(watchdog_alerts, watchdog_warnings, watchdog_incidents))
        recs.extend(self.from_reasoning(reasoning_failures, active_sessions))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recs.sort(key=lambda r: priority_order.get(r.priority, 99))

        self._recommendations.extend(recs)
        if len(self._recommendations) > self._max_recommendations:
            self._recommendations = self._recommendations[-self._max_recommendations:]

        return recs

    @property
    def recommendations(self) -> List[GuardianRecommendation]:
        return list(self._recommendations)

    def clear(self) -> None:
        self._recommendations.clear()
