"""
OP-336 — Conversation Guardian V2

10 query read-only untuk guardian:
  summary, trend, health, policy, recommendation,
  finding, risk, timeline, snapshot, status
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianV2Response:
    """Response untuk query Conversation V2."""
    success: bool
    query_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: str = ""

    @staticmethod
    def error(query_type: str, message: str) -> GuardianV2Response:
        return GuardianV2Response(
            success=False, query_type=query_type,
            message=message, timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    @staticmethod
    def ok(query_type: str, data: Dict[str, Any], message: str = "") -> GuardianV2Response:
        return GuardianV2Response(
            success=True, query_type=query_type, data=data,
            message=message, timestamp=datetime.now().isoformat(timespec="seconds"),
        )


class GuardianConversationV2:
    """Conversation API V2 — 10 query read-only."""

    def __init__(
        self,
        snapshot_engine: Any = None,
        health_engine: Any = None,
        policy_evaluator: Any = None,
        recommendation_engine: Any = None,
        trend_analyzer: Any = None,
        history: Any = None,
        summary_builder: Any = None,
        supervisor: Any = None,
        watchdog: Any = None,
    ):
        self._snapshot = snapshot_engine
        self._health = health_engine
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._trend = trend_analyzer
        self._history = history
        self._summary = summary_builder
        self._supervisor = supervisor
        self._watchdog = watchdog
        self._query_history: List[str] = []

    @property
    def query_history(self) -> Tuple[str, ...]:
        return tuple(self._query_history)

    def _log(self, query: str) -> None:
        self._query_history.append("{}:{}".format(
            datetime.now().isoformat(timespec="seconds"), query,
        ))

    # ── 1. Guardian Summary ──

    def query_summary(self) -> GuardianV2Response:
        """Summary: current health, findings, violations, recs, risks, priorities."""
        self._log("summary")
        sm = self._summary.last_summary if self._summary else None
        if sm:
            return GuardianV2Response.ok("summary", sm.to_dict())
        return GuardianV2Response.error("summary", "No summary available")

    # ── 2. Guardian Trend ──

    def query_trend(self) -> GuardianV2Response:
        """Trend: health, recommendation, watchdog, policy, anomaly."""
        self._log("trend")
        t = self._trend.last_trend if self._trend else None
        if t:
            return GuardianV2Response.ok("trend", t.to_dict())
        return GuardianV2Response.error("trend", "No trend data available")

    # ── 3. Guardian Health ──

    def query_health(self) -> GuardianV2Response:
        """Health: status, score, issues."""
        self._log("health")
        h = self._health.latest() if self._health else None
        if h:
            return GuardianV2Response.ok("health", {
                "status": h.status,
                "overall_score": h.score.overall_score,
                "issues_count": len(h.issues),
                "issues": [
                    {"component": i.component, "severity": i.severity, "message": i.message}
                    for i in h.issues
                ],
            })
        return GuardianV2Response.error("health", "No health data available")

    # ── 4. Guardian Policy ──

    def query_policy(self) -> GuardianV2Response:
        """Policy: all_passed, violations, results."""
        self._log("policy")
        if not self._policy:
            return GuardianV2Response.error("policy", "Policy evaluator not available")
        return GuardianV2Response.ok("policy", {
            "all_passed": self._policy.all_passed,
            "violations_count": len(self._policy.violations),
            "violations": [
                {"policy": v.policy, "severity": v.severity, "message": v.message}
                for v in self._policy.violations
            ],
        })

    # ── 5. Guardian Recommendation ──

    def query_recommendation(self) -> GuardianV2Response:
        """Recommendations: count, details."""
        self._log("recommendation")
        if not self._recommendation:
            return GuardianV2Response.error("recommendation", "Recommendation engine not available")
        recs = self._recommendation.recommendations
        return GuardianV2Response.ok("recommendation", {
            "count": len(recs),
            "recommendations": [
                {"type": r.recommendation_type, "priority": r.priority,
                 "source": r.source, "title": r.title}
                for r in recs
            ],
        })

    # ── 6. Guardian Finding ──

    def query_finding(self) -> GuardianV2Response:
        """Findings: policy violations + watchdog alerts/warnings."""
        self._log("finding")
        findings: List[Dict[str, Any]] = []

        if self._policy:
            for v in self._policy.violations:
                findings.append({
                    "category": "policy", "severity": v.severity,
                    "message": "{}: {}".format(v.policy, v.message),
                })
        if self._watchdog:
            for a in self._watchdog.alerts:
                findings.append({
                    "category": "watchdog_alert", "severity": a.severity,
                    "message": "{}: {}".format(a.alert_type, a.message),
                })
            for w in self._watchdog.warnings:
                findings.append({
                    "category": "watchdog_warning", "severity": "medium",
                    "message": "{}: {}".format(w.warning_type, w.message),
                })

        return GuardianV2Response.ok("finding", {
            "count": len(findings),
            "findings": findings,
        })

    # ── 7. Guardian Risk ──

    def query_risk(self) -> GuardianV2Response:
        """Risks: dari trend signals & patterns."""
        self._log("risk")
        t = self._trend.last_trend if self._trend else None
        risks: Dict[str, Any] = {
            "signals": [],
            "patterns": [],
        }
        if t:
            risks["signals"] = list(t.signals)
            risks["patterns"] = list(t.patterns)
        risks["count"] = len(risks["signals"]) + len(risks["patterns"])
        return GuardianV2Response.ok("risk", risks)

    # ── 8. Guardian Timeline ──

    def query_timeline(self, limit: int = 20) -> GuardianV2Response:
        """Timeline: events dari history."""
        self._log("timeline")
        if not self._history:
            return GuardianV2Response.error("timeline", "History not available")
        events = self._history.latest(limit)
        return GuardianV2Response.ok("timeline", {
            "count": len(events),
            "events": [e.to_dict() for e in events],
        })

    # ── 9. Guardian Snapshot ──

    def query_snapshot(self) -> GuardianV2Response:
        """Snapshot: latest snapshot dari snapshot engine."""
        self._log("snapshot")
        snap = self._snapshot.last_snapshot if self._snapshot else None
        if snap:
            return GuardianV2Response.ok("snapshot", snap.to_dict())
        return GuardianV2Response.error("snapshot", "No snapshot available")

    # ── 10. Guardian Status ──

    def query_status(self) -> GuardianV2Response:
        """Status: gabungan dari berbagai sumber."""
        self._log("status")
        data: Dict[str, Any] = {}

        # Health
        h = self._health.latest() if self._health else None
        data["health_status"] = h.status if h else "unknown"

        # Snapshot
        snap = self._snapshot.last_snapshot if self._snapshot else None
        data["system_status"] = snap.system_status if snap else "unknown"

        # Supervisor
        if self._supervisor:
            data["supervisor_issues"] = self._supervisor.has_overall_issues

        # Policy
        if self._policy:
            data["all_policies_passed"] = self._policy.all_passed
            data["policy_violations"] = len(self._policy.violations)

        # Watchdog
        if self._watchdog:
            data["watchdog_alerts"] = len(self._watchdog.alerts)
            data["watchdog_warnings"] = len(self._watchdog.warnings)

        # History
        if self._history:
            data["history_events"] = self._history.event_count

        # Trend
        t = self._trend.last_trend if self._trend else None
        if t:
            data["health_trend"] = t.health_trend
            data["anomaly_trend"] = t.anomaly_trend

        return GuardianV2Response.ok("status", data)
