"""
OP-243 — Operational Analyzer.

Takes ObservationSnapshot + TriggeredRules and produces OperationalFindings.
Each finding has severity, confidence, evidence, affected resources, and recommended actions.
Does NOT create missions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .observation_engine import ObservationSnapshot
from .rule_engine import TriggeredRule


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class OperationalFinding:
    """A structured finding produced by the analyzer."""

    finding_id: str
    title: str
    description: str
    severity: Severity
    confidence: float  # 0.0 - 1.0
    evidence: List[Dict[str, Any]]
    affected_resources: List[str]
    recommended_actions: List[str]
    source_rules: List[str]
    timestamp: float


class OperationalAnalyzer:
    """Analyzes operational state and triggered rules into findings.

    Each finding is evidence-based and includes confidence scoring.
    """

    def __init__(self) -> None:
        self._last_findings: List[OperationalFinding] = []

    def analyze(
        self,
        snapshot: ObservationSnapshot,
        triggered_rules: List[TriggeredRule],
    ) -> List[OperationalFinding]:
        """Produce findings from snapshot + rules.

        Rules map to findings. Multiple rules may contribute to one finding.
        """
        import time
        findings: List[OperationalFinding] = []

        # Group triggered rules by logical clusters
        rule_map = {r.rule_id: r for r in triggered_rules}

        # ── Pending approvals finding ─────────────────────────────
        if "high_pending_approvals" in rule_map:
            r = rule_map["high_pending_approvals"]
            evidence = [
                {"type": "rule_trigger", "rule_id": r.rule_id, "value": snapshot.pending_approvals},
                {"type": "observation", "field": "pending_approvals", "value": snapshot.pending_approvals},
            ]
            findings.append(OperationalFinding(
                finding_id="approval_backlog",
                title="Approval Backlog",
                description=f"{snapshot.pending_approvals} approvals are pending — may delay operations",
                severity=Severity.WARNING,
                confidence=0.85,
                evidence=evidence,
                affected_resources=["approval"],
                recommended_actions=[
                    "Review pending approvals",
                    "Prioritize by urgency",
                ],
                source_rules=["high_pending_approvals"],
                timestamp=time.time(),
            ))

        # ── Mission failure finding ───────────────────────────────
        has_failure = "failed_missions" in rule_map or "repeated_failure" in rule_map
        if has_failure:
            evidence = [
                {"type": "observation", "field": "failed_missions", "value": snapshot.failed_missions},
                {"type": "observation", "field": "active_missions", "value": snapshot.active_missions},
            ]
            rules = []
            if "failed_missions" in rule_map:
                rules.append("failed_missions")
            if "repeated_failure" in rule_map:
                rules.append("repeated_failure")
            findings.append(OperationalFinding(
                finding_id="mission_failure",
                title="Mission Failure Detected",
                description=f"{snapshot.failed_missions} failed mission(s) — requires investigation",
                severity=Severity.CRITICAL,
                confidence=0.95,
                evidence=evidence,
                affected_resources=["mission"],
                recommended_actions=[
                    "Open Mission Inspector to review failures",
                    "Check recovery options for each failed mission",
                    "Assess root cause",
                ],
                source_rules=rules,
                timestamp=time.time(),
            ))

        # ── Queue finding ─────────────────────────────────────────
        if "queue_stalled" in rule_map:
            evidence = [
                {"type": "rule_trigger", "rule_id": "queue_stalled", "value": snapshot.queue_length},
            ]
            findings.append(OperationalFinding(
                finding_id="queue_stall",
                title="Operation Queue Stalled",
                description=f"Queue length is {snapshot.queue_length} — operations may be blocked",
                severity=Severity.WARNING,
                confidence=0.75,
                evidence=evidence,
                affected_resources=["operations", "queue"],
                recommended_actions=[
                    "Check queue for stuck items",
                    "Consider clearing stalled operations",
                ],
                source_rules=["queue_stalled"],
                timestamp=time.time(),
            ))

        # ── Trust finding ─────────────────────────────────────────
        if "low_trust" in rule_map:
            evidence = [
                {"type": "observation", "field": "trust_summary", "value": dict(snapshot.trust_summary)},
            ]
            low_items = [
                k for k, v in snapshot.trust_summary.items() if v < 0.5
            ]
            findings.append(OperationalFinding(
                finding_id="trust_degradation",
                title="Trust Score Degradation",
                description=f"Low trust in: {', '.join(low_items)}",
                severity=Severity.CRITICAL,
                confidence=0.90,
                evidence=evidence,
                affected_resources=["trust"] + low_items,
                recommended_actions=[
                    "Review trust history for affected components",
                    "Investigate trust degradation root cause",
                ],
                source_rules=["low_trust"],
                timestamp=time.time(),
            ))

        # ── Lock finding ──────────────────────────────────────────
        if "lock_timeout" in rule_map:
            evidence = [
                {"type": "observation", "field": "locks_held", "value": snapshot.locks_held},
            ]
            findings.append(OperationalFinding(
                finding_id="lock_contention",
                title="Workspace Lock Contention",
                description=f"{snapshot.locks_held} locks held — potential contention",
                severity=Severity.WARNING,
                confidence=0.70,
                evidence=evidence,
                affected_resources=["workspace"],
                recommended_actions=[
                    "Review active locks",
                    "Release stale locks if safe",
                ],
                source_rules=["lock_timeout"],
                timestamp=time.time(),
            ))

        # ── Anomaly finding ───────────────────────────────────────
        if "high_anomaly_count" in rule_map:
            anomaly_details = snapshot.anomalies[:5]
            evidence = [
                {"type": "observation", "field": "anomaly_count", "value": len(snapshot.anomalies)},
                {"type": "observation", "field": "anomaly_details", "value": anomaly_details},
            ]
            findings.append(OperationalFinding(
                finding_id="anomaly_cluster",
                title="Anomaly Cluster Detected",
                description=f"{len(snapshot.anomalies)} anomalies in recent window",
                severity=Severity.CRITICAL,
                confidence=0.85,
                evidence=evidence,
                affected_resources=["telemetry", "intelligence"],
                recommended_actions=[
                    "Open Timeline Explorer to view anomalies",
                    "Assess if anomalies are related",
                    "Check for systemic issues",
                ],
                source_rules=["high_anomaly_count"],
                timestamp=time.time(),
            ))

        # ── Notification finding ──────────────────────────────────
        if "notification_alert" in rule_map:
            evidence = [
                {"type": "observation", "field": "notification_summary", "value": dict(snapshot.notification_summary)},
            ]
            findings.append(OperationalFinding(
                finding_id="notification_alert",
                title="Error Notifications Present",
                description=f"{snapshot.notification_summary.get('error', 0)} error notification(s)",
                severity=Severity.WARNING,
                confidence=0.80,
                evidence=evidence,
                affected_resources=["notification"],
                recommended_actions=[
                    "Open Notification Center",
                    "Review and acknowledge error notifications",
                ],
                source_rules=["notification_alert"],
                timestamp=time.time(),
            ))

        # ── Idle finding ──────────────────────────────────────────
        if "no_active_missions" in rule_map and not has_failure:
            evidence = [
                {"type": "observation", "field": "active_missions", "value": 0},
            ]
            findings.append(OperationalFinding(
                finding_id="system_idle",
                title="System Idle — No Active Missions",
                description="No missions currently running. System is idle.",
                severity=Severity.INFO,
                confidence=1.0,
                evidence=evidence,
                affected_resources=["mission"],
                recommended_actions=[
                    "Consider starting a new mission",
                    "Check scheduled tasks",
                ],
                source_rules=["no_active_missions"],
                timestamp=time.time(),
            ))

        self._last_findings = findings
        return findings

    @property
    def last_findings(self) -> List[OperationalFinding]:
        return list(self._last_findings)


def analyze(
    snapshot: ObservationSnapshot,
    triggered_rules: List[TriggeredRule],
) -> List[OperationalFinding]:
    """One-shot convenience."""
    return OperationalAnalyzer().analyze(snapshot, triggered_rules)
