"""
OP-244 — Recommendation Builder.

Converts OperationalFindings into MissionRecommendation DTOs.
Does NOT create missions — only produces recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .analyzer import OperationalFinding, Severity


@dataclass
class MissionRecommendation:
    """A recommendation that could become a mission (requires approval)."""

    recommendation_id: str
    title: str
    description: str
    priority: str  # "low" | "medium" | "high" | "critical"
    estimated_impact: str
    required_approval: bool
    evidence: List[Dict[str, Any]]
    suggested_steps: List[str]
    source_finding_id: str
    confidence: float  # 0.0 - 1.0
    timestamp: float


_PRIORITY_MAP = {
    Severity.INFO: "low",
    Severity.WARNING: "medium",
    Severity.CRITICAL: "high",
}

_ESTIMATED_IMPACT_MAP = {
    "approval_backlog": "Low — unblocks pending approvals",
    "mission_failure": "High — restores failed mission operations",
    "queue_stall": "Medium — re-enables operation queue",
    "trust_degradation": "High — restores trust in critical components",
    "lock_contention": "Low — releases workspace contention",
    "anomaly_cluster": "High — investigates potential systemic issues",
    "notification_alert": "Medium — clears error notification backlog",
    "system_idle": "Low — system is idle, no action required",
}

_STEPS_MAP = {
    "approval_backlog": [
        "Open Approval Dialog",
        "Review pending approvals sorted by urgency",
        "Approve or reject with reason",
    ],
    "mission_failure": [
        "Open Mission Inspector to failed missions",
        "Review failure details and recovery options",
        "Execute recovery plan or restart mission",
    ],
    "queue_stall": [
        "Open Operations Queue",
        "Identify stalled operations",
        "Clear or restart stalled operations",
    ],
    "trust_degradation": [
        "Open Trust Dashboard",
        "Review trust history for affected components",
        "Take corrective action to restore trust",
    ],
    "lock_contention": [
        "Open Workspace Locks view",
        "Identify stale locks",
        "Release locks that are no longer needed",
    ],
    "anomaly_cluster": [
        "Open Timeline Explorer filtered to anomalies",
        "Review anomaly details and correlations",
        "Escalate if systemic pattern detected",
    ],
    "notification_alert": [
        "Open Notification Center",
        "Review error notifications",
        "Acknowledge or escalate",
    ],
    "system_idle": [
        "Review scheduled missions",
        "Start a new mission if appropriate",
    ],
}


class RecommendationBuilder:
    """Builds MissionRecommendations from OperationalFindings.

    Pure transformation — no side effects.
    """

    def __init__(self) -> None:
        self._last_recommendations: List[MissionRecommendation] = []

    def build(self, findings: List[OperationalFinding]) -> List[MissionRecommendation]:
        """Convert findings to recommendations.

        Only INFO+ findings produce recommendations.
        """
        import time
        recommendations: List[MissionRecommendation] = []

        for f in findings:
            if f.severity == Severity.INFO:
                continue  # info findings are informational, no action needed

            rec = MissionRecommendation(
                recommendation_id=f"rec_{f.finding_id}",
                title=f"Recommendation: {f.title}",
                description=f.description,
                priority=_PRIORITY_MAP.get(f.severity, "medium"),
                estimated_impact=_ESTIMATED_IMPACT_MAP.get(
                    f.finding_id, "Unknown impact"
                ),
                required_approval=True,
                evidence=list(f.evidence),
                suggested_steps=list(
                    _STEPS_MAP.get(f.finding_id, ["Assess situation", "Take corrective action"])
                ),
                source_finding_id=f.finding_id,
                confidence=f.confidence,
                timestamp=time.time(),
            )
            recommendations.append(rec)

        self._last_recommendations = recommendations
        return recommendations

    @property
    def last_recommendations(self) -> List[MissionRecommendation]:
        return list(self._last_recommendations)


def build_recommendations(
    findings: List[OperationalFinding],
) -> List[MissionRecommendation]:
    """One-shot convenience."""
    return RecommendationBuilder().build(findings)
