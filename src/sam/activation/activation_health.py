"""Activation Health — kesehatan proses aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_metrics import ActivationMetrics
from sam.activation.activation_snapshot import ActivationSnapshotState


@dataclass(frozen=True)
class ActivationHealthReport:
    healthy: bool = False
    package_count: int = 0
    avg_confidence: float = 0.0
    event_count: int = 0
    issues: List[str] = field(default_factory=list)
    score: float = 0.0


class ActivationHealthChecker:
    """Memeriksa kesehatan aktivasi — pure function."""

    def check(self, snapshot: ActivationSnapshotState) -> ActivationHealthReport:
        issues: List[str] = []
        score = 1.0

        if snapshot.total_packages == 0:
            issues.append("No packages")
            score -= 0.3

        metrics = snapshot.metrics
        avg_conf = metrics.avg_confidence if metrics else 0.0
        if avg_conf < 0.5:
            issues.append("Low confidence")
            score -= 0.2

        if snapshot.total_events == 0:
            issues.append("No events recorded")
            score -= 0.1

        if snapshot.total_history == 0:
            issues.append("No history")
            score -= 0.1

        return ActivationHealthReport(
            healthy=score >= 0.5 and snapshot.total_packages > 0,
            package_count=snapshot.total_packages,
            avg_confidence=avg_conf,
            event_count=snapshot.total_events,
            issues=issues,
            score=round(max(0, score), 2),
        )
