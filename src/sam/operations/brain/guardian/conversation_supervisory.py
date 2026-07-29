"""
OP-326 — Guardian Conversation

Conversation API baru untuk guardian, read-only:
  - guardian health
  - guardian issues
  - guardian recommendations
  - guardian providers
  - guardian trust
  - guardian status
  - guardian queue
  - guardian summary

Semua read-only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianConversationQuery:
    query_type: str
    detail: str = ""
    timestamp: str = ""


@dataclass(frozen=True)
class GuardianConversationResponse:
    query_type: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type,
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class GuardianSupervisoryConversation:
    """
    Read-only conversation API untuk Guardian Supervisor.
    """

    def __init__(
        self,
        health_engine: Any,
        supervisor: Any,
        watchdog: Any,
        policy_evaluator: Any,
        recommendation_engine: Any,
    ) -> None:
        self._health = health_engine
        self._supervisor = supervisor
        self._watchdog = watchdog
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._queries: List[GuardianConversationQuery] = []
        self._max_queries: int = 50

    def _log_query(self, query_type: str, detail: str = "") -> None:
        self._queries.append(GuardianConversationQuery(
            query_type=query_type,
            detail=detail,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        ))
        if len(self._queries) > self._max_queries:
            self._queries = self._queries[-self._max_queries:]

    def get_health(self) -> GuardianConversationResponse:
        self._log_query("health")
        latest = self._health.latest()
        if latest:
            data = latest.to_dict()
        else:
            data = {"status": "unknown", "message": "No health data available"}
        return GuardianConversationResponse(
            query_type="health",
            success=True,
            data=data,
            message="Guardian health status",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_issues(self) -> GuardianConversationResponse:
        self._log_query("issues")
        issues: List[Dict[str, Any]] = []

        health = self._health.latest()
        if health:
            issues.extend(i.to_dict() for i in health.issues)

        violations = self._policy.violations
        issues.extend(v.to_dict() for v in violations)

        alerts = self._watchdog.alerts
        issues.extend(a.to_dict() for a in alerts)

        incidents = self._watchdog.incidents
        issues.extend(i.to_dict() for i in incidents)

        return GuardianConversationResponse(
            query_type="issues",
            success=True,
            data={"issues": issues, "count": len(issues)},
            message="Guardian issues",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_recommendations(self) -> GuardianConversationResponse:
        self._log_query("recommendations")
        recs = self._recommendation.recommendations
        return GuardianConversationResponse(
            query_type="recommendations",
            success=True,
            data={
                "recommendations": [r.to_dict() for r in recs],
                "count": len(recs),
            },
            message="Guardian recommendations",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_providers(self) -> GuardianConversationResponse:
        self._log_query("providers")
        snapshot = self._supervisor.latest()
        data: Dict[str, Any] = {"status": "unknown"}
        if snapshot:
            data = {
                "active": snapshot.provider.active_providers,
                "healthy": snapshot.provider.healthy_providers,
                "degraded": snapshot.provider.degraded_providers,
                "last_check": snapshot.provider.last_check_at,
            }
        return GuardianConversationResponse(
            query_type="providers",
            success=True,
            data=data,
            message="Provider status",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_trust(self) -> GuardianConversationResponse:
        self._log_query("trust")
        health = self._health.latest()
        trust_score = 1.0
        if health:
            trust_score = health.score.trust_score
        return GuardianConversationResponse(
            query_type="trust",
            success=True,
            data={"trust_score": round(trust_score, 2)},
            message="Trust level",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_status(self) -> GuardianConversationResponse:
        self._log_query("status")
        snapshot = self._supervisor.latest()
        health = self._health.latest()
        data: Dict[str, Any] = {
            "supervisor_issues": self._supervisor.has_overall_issues if snapshot else False,
            "health_status": health.status if health else "unknown",
            "policies_passed": self._policy.all_passed,
            "policy_violations": len(self._policy.violations),
            "recommendations": len(self._recommendation.recommendations),
        }
        if snapshot:
            data["snapshot"] = snapshot.to_dict()
        return GuardianConversationResponse(
            query_type="status",
            success=True,
            data=data,
            message="Guardian status summary",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_queue(self) -> GuardianConversationResponse:
        self._log_query("queue")
        snapshot = self._supervisor.latest()
        data: Dict[str, Any] = {"status": "unknown"}
        if snapshot:
            data = {
                "tasks_queued": snapshot.scheduler.tasks_queued,
                "tasks_running": snapshot.scheduler.tasks_running,
                "tasks_completed": snapshot.scheduler.tasks_completed,
                "overloaded": snapshot.scheduler.overloaded,
            }
        return GuardianConversationResponse(
            query_type="queue",
            success=True,
            data=data,
            message="Queue status",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def get_summary(self) -> GuardianConversationResponse:
        self._log_query("summary")
        health = self._health.latest()
        snapshot = self._supervisor.latest()
        data: Dict[str, Any] = {
            "health": health.status if health else "unknown",
            "supervisor_issues": self._supervisor.has_overall_issues if snapshot else False,
            "policies_passed": self._policy.all_passed,
            "total_recommendations": len(self._recommendation.recommendations),
            "total_violations": len(self._policy.violations),
            "total_watchdog_alerts": len(self._watchdog.alerts),
            "total_watchdog_incidents": len(self._watchdog.incidents),
        }
        return GuardianConversationResponse(
            query_type="summary",
            success=True,
            data=data,
            message="Guardian summary",
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    @property
    def query_history(self) -> List[GuardianConversationQuery]:
        return list(self._queries)
