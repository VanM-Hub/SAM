"""
OP-242 — Rule Engine.

Simple IF-THEN rules that detect conditions.
Rules never execute actions — only produce TriggeredRule records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .observation_engine import ObservationSnapshot


@dataclass
class RuleDef:
    """Definition of a single rule."""

    rule_id: str
    name: str
    description: str
    severity: str  # "info" | "warning" | "critical"
    check_fn: Callable[[ObservationSnapshot], bool]
    params: Optional[Dict[str, Any]] = None


@dataclass
class TriggeredRule:
    """A rule that fired."""

    rule_id: str
    name: str
    description: str
    severity: str
    snapshot_value: Any
    threshold: Optional[Any]
    timestamp: float


def _import_time():
    import time  # noqa
    return time


class RuleEngine:
    """Evaluates rules against an ObservationSnapshot.

    Rules are registered via add_rule() or as builtins.
    Output: list of TriggeredRule (zero or more).
    """

    def __init__(self) -> None:
        self._rules: List[RuleDef] = []
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register default built-in rules."""
        self._rules = [
            RuleDef(
                rule_id="high_pending_approvals",
                name="High Pending Approvals",
                description="Pending approvals exceed threshold",
                severity="warning",
                check_fn=lambda snap: snap.pending_approvals >= 5,
            ),
            RuleDef(
                rule_id="failed_missions",
                name="Failed Missions Detected",
                description="One or more missions have failed",
                severity="critical",
                check_fn=lambda snap: snap.failed_missions > 0,
            ),
            RuleDef(
                rule_id="queue_stalled",
                name="Queue Stalled",
                description="Operation queue has stalled (no progress)",
                severity="warning",
                check_fn=lambda snap: snap.queue_length >= 20,
            ),
            RuleDef(
                rule_id="low_trust",
                name="Low Trust Score",
                description="Trust level below minimum threshold",
                severity="critical",
                check_fn=lambda snap: any(
                    score < 0.5 for score in snap.trust_summary.values()
                ),
            ),
            RuleDef(
                rule_id="lock_timeout",
                name="Lock Timeout Risk",
                description="Multiple workspace locks held",
                severity="warning",
                check_fn=lambda snap: snap.locks_held >= 3,
            ),
            RuleDef(
                rule_id="repeated_failure",
                name="Repeated Failure Pattern",
                description="High number of active failures suggests systemic issue",
                severity="critical",
                check_fn=lambda snap: snap.failed_missions >= 3,
            ),
            RuleDef(
                rule_id="high_anomaly_count",
                name="Anomaly Cluster Detected",
                description="Multiple anomalies in recent window",
                severity="critical",
                check_fn=lambda snap: len(snap.anomalies) >= 3,
            ),
            RuleDef(
                rule_id="notification_alert",
                name="Notification Alert",
                description="Error notifications present",
                severity="warning",
                check_fn=lambda snap: snap.notification_summary.get("error", 0) > 0,
            ),
            RuleDef(
                rule_id="high_telemetry_rate",
                name="High Telemetry Rate",
                description="Telemetry event rate above normal threshold",
                severity="info",
                check_fn=lambda snap: snap.telemetry_summary.get("rate_per_min", 0.0) > 100.0,
            ),
            RuleDef(
                rule_id="no_active_missions",
                name="No Active Missions",
                description="No missions currently running",
                severity="info",
                check_fn=lambda snap: snap.active_missions == 0,
            ),
        ]

    def add_rule(self, rule: RuleDef) -> None:
        """Register a custom rule."""
        self._rules.append(rule)

    @property
    def rules(self) -> List[RuleDef]:
        return list(self._rules)

    def evaluate(self, snapshot: ObservationSnapshot) -> List[TriggeredRule]:
        """Evaluate all rules against a snapshot.

        Returns list of triggered rules (empty if none).
        """
        import time
        triggered: List[TriggeredRule] = []
        for rule in self._rules:
            try:
                if rule.check_fn(snapshot):
                    triggered.append(TriggeredRule(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        description=rule.description,
                        severity=rule.severity,
                        snapshot_value=self._get_value(snapshot, rule),
                        threshold=rule.params.get("threshold") if rule.params else None,
                        timestamp=time.time(),
                    ))
            except Exception:
                continue
        return triggered

    @staticmethod
    def _get_value(snapshot: ObservationSnapshot, rule: RuleDef) -> Any:
        """Extract relevant value from snapshot for a rule."""
        mapping = {
            "high_pending_approvals": snapshot.pending_approvals,
            "failed_missions": snapshot.failed_missions,
            "queue_stalled": snapshot.queue_length,
            "low_trust": snapshot.trust_summary,
            "lock_timeout": snapshot.locks_held,
            "repeated_failure": snapshot.failed_missions,
            "high_anomaly_count": len(snapshot.anomalies),
            "notification_alert": snapshot.notification_summary.get("error", 0),
            "high_telemetry_rate": snapshot.telemetry_summary.get("rate_per_min", 0.0),
            "no_active_missions": snapshot.active_missions,
        }
        return mapping.get(rule.rule_id, None)


def evaluate_rules(snapshot: ObservationSnapshot) -> List[TriggeredRule]:
    """One-shot convenience."""
    return RuleEngine().evaluate(snapshot)
