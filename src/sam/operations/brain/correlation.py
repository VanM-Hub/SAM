"""
OP-253 — Correlation Engine.

Correlates OperationalFindings from the Analyzer into CorrelationGroups
using rule-based logic. Findings are related if they share evidence,
resources, or follow known patterns.

Pure transformation — no side effects.
Only rule-based — no statistics, AI, or ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .analyzer import OperationalFinding


@dataclass
class CorrelationDef:
    """Definition of a correlation rule."""

    correlation_id: str
    name: str
    description: str
    required_finding_ids: List[str]  # all must be present
    min_confidence: float = 0.0

    def matches(self, finding_ids: set) -> bool:
        return set(self.required_finding_ids).issubset(finding_ids)


@dataclass
class CorrelatedFinding:
    """A group of related findings."""

    correlation_id: str
    name: str
    description: str
    confidence: float
    explanation: str
    related_findings: List[OperationalFinding]
    shared_evidence: List[Dict[str, Any]]

    @property
    def severity(self) -> str:
        """Highest severity among related findings."""
        severities = {f.severity.value for f in self.related_findings}
        if "critical" in severities:
            return "critical"
        if "warning" in severities:
            return "warning"
        return "info"

    def __repr__(self) -> str:
        return (
            f"CorrelatedFinding({self.correlation_id}: "
            f"{self.name}, {len(self.related_findings)} findings, "
            f"conf={self.confidence:.2f})"
        )


# ── Built-in correlation rules ────────────────────────────────────────

_BUILTIN_CORRELATIONS: List[CorrelationDef] = [
    CorrelationDef(
        correlation_id="governance_issue",
        name="Potential Governance Issue",
        description="Approval backlog combined with trust degradation suggests governance risk",
        required_finding_ids=["approval_backlog", "trust_degradation"],
        min_confidence=0.6,
    ),
    CorrelationDef(
        correlation_id="systemic_failure",
        name="Systemic Failure Pattern",
        description="Multiple mission failures with anomalies suggest systemic issue",
        required_finding_ids=["mission_failure", "anomaly_cluster"],
        min_confidence=0.7,
    ),
    CorrelationDef(
        correlation_id="operational_gridlock",
        name="Operational Gridlock",
        description="Queue stalled with lock contention and approval backlog blocks progress",
        required_finding_ids=["queue_stall", "lock_contention", "approval_backlog"],
        min_confidence=0.5,
    ),
    CorrelationDef(
        correlation_id="approval_cascade",
        name="Approval Cascade Risk",
        description="Notification alerts with pending approvals suggest cascading delays",
        required_finding_ids=["notification_alert", "approval_backlog"],
        min_confidence=0.5,
    ),
    CorrelationDef(
        correlation_id="trust_crisis",
        name="Trust Crisis Risk",
        description="Multiple failures with degraded trust signal a trust crisis",
        required_finding_ids=["trust_degradation", "mission_failure"],
        min_confidence=0.6,
    ),
    CorrelationDef(
        correlation_id="idle_with_alerts",
        name="Idle System with Alerts",
        description="System idle but errors persist — may need maintenance",
        required_finding_ids=["system_idle", "notification_alert"],
        min_confidence=0.4,
    ),
]


class CorrelationEngine:
    """Correlates findings into groups using rule-based matching.

    Rules require specific finding IDs to all be present.
    CorrelationGroups include shared evidence and explanations.
    """

    def __init__(self) -> None:
        self._correlations: List[CorrelationDef] = list(_BUILTIN_CORRELATIONS)
        self._last_groups: List[CorrelatedFinding] = []

    @property
    def correlations(self) -> List[CorrelationDef]:
        return list(self._correlations)

    def add_correlation(self, corr: CorrelationDef) -> None:
        """Register a custom correlation rule."""
        self._correlations.append(corr)

    def correlate(
        self,
        findings: List[OperationalFinding],
    ) -> List[CorrelatedFinding]:
        """Run all correlation rules against findings.

        Returns list of CorrelatedFinding (empty if no correlations).
        """
        finding_map = {f.finding_id: f for f in findings}
        finding_ids = set(finding_map.keys())
        groups: List[CorrelatedFinding] = []

        for corr in self._correlations:
            if not corr.matches(finding_ids):
                continue

            matched = [
                finding_map[fid]
                for fid in corr.required_finding_ids
                if fid in finding_map
            ]
            if not matched:
                continue

            # Shared evidence = union of all evidence from matched findings
            shared_evidence: List[Dict[str, Any]] = []
            seen: set = set()
            for f in matched:
                for ev in f.evidence:
                    key = str(ev)
                    if key not in seen:
                        seen.add(key)
                        shared_evidence.append(ev)

            # Confidence = average of matched findings
            avg_confidence = sum(f.confidence for f in matched) / len(matched)

            # Build human-readable explanation
            finding_names = [f.title for f in matched]
            explanation = (
                f"{corr.description}. "
                f"Triggered by: {' + '.join(finding_names)}."
            )

            groups.append(CorrelatedFinding(
                correlation_id=corr.correlation_id,
                name=corr.name,
                description=corr.description,
                confidence=round(min(avg_confidence, 1.0), 2),
                explanation=explanation,
                related_findings=matched,
                shared_evidence=shared_evidence,
            ))

        self._last_groups = groups
        return groups

    @property
    def last_groups(self) -> List[CorrelatedFinding]:
        return list(self._last_groups)


# ── Helper ────────────────────────────────────────────────────────────


def build_finding_dict(
    findings: List[OperationalFinding],
) -> Dict[str, OperationalFinding]:
    """Build a finding_id -> finding lookup dict."""
    return {f.finding_id: f for f in findings}


# ── Convenience ───────────────────────────────────────────────────────


def correlate_findings(
    findings: List[OperationalFinding],
) -> List[CorrelatedFinding]:
    """One-shot convenience."""
    return CorrelationEngine().correlate(findings)
