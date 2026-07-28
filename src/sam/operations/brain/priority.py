"""
OP-254 — Priority Engine.

Assigns priority scores (0–100) and categories (CRITICAL–INFO)
to OperationalFindings based on severity, impact, confidence,
trust, age, dependency, resource count, and trend.

Pure transformation — no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .analyzer import OperationalFinding, Severity


class PriorityCategory(Enum):
    """Priority categories derived from score."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PriorityConfig:
    """Scoring weights and thresholds."""

    severity_weight: float = 0.35
    impact_weight: float = 0.20
    confidence_weight: float = 0.15
    trust_weight: float = 0.10
    age_weight: float = 0.05
    dependency_weight: float = 0.05
    resource_weight: float = 0.05
    trend_weight: float = 0.05

    # Severity base scores
    critical_base: float = 90.0
    warning_base: float = 60.0
    info_base: float = 30.0

    # Category thresholds
    critical_threshold: float = 80.0
    high_threshold: float = 60.0
    medium_threshold: float = 40.0
    low_threshold: float = 20.0


_DEFAULT_CONFIG = PriorityConfig()


@dataclass
class PriorityScore:
    """Calculated priority for a finding."""

    finding_id: str
    score: float  # 0–100
    category: PriorityCategory
    components: Dict[str, float] = field(default_factory=dict)

    @property
    def category_value(self) -> str:
        return self.category.value

    @property
    def is_actionable(self) -> bool:
        return self.category in (
            PriorityCategory.CRITICAL,
            PriorityCategory.HIGH,
            PriorityCategory.MEDIUM,
        )

    def __repr__(self) -> str:
        return (
            f"PriorityScore({self.finding_id}: "
            f"{self.score:.0f}/{self.category_value})"
        )


def _severity_base(severity: Severity, config: PriorityConfig) -> float:
    mapping = {
        Severity.CRITICAL: config.critical_base,
        Severity.WARNING: config.warning_base,
        Severity.INFO: config.info_base,
    }
    return mapping.get(severity, config.info_base)


def _estimate_impact_score(finding: OperationalFinding) -> float:
    """Estimate impact score (0–100) from finding context."""
    high_impact_ids = {
        "mission_failure",
        "trust_degradation",
        "anomaly_cluster",
    }
    medium_impact_ids = {
        "queue_stall",
        "notification_alert",
    }
    if finding.finding_id in high_impact_ids:
        return 80.0
    if finding.finding_id in medium_impact_ids:
        return 50.0
    return 20.0


def _estimate_resource_score(finding: OperationalFinding) -> float:
    """More affected resources = higher score."""
    count = len(finding.affected_resources)
    if count >= 4:
        return 80.0
    if count >= 2:
        return 50.0
    return 20.0


def _estimate_trend_score(finding: OperationalFinding) -> float:
    """Simple trend: recurring findings get higher score."""
    # Currently static — future versions can track historical frequency
    return 50.0


def _estimate_dependency_score(finding: OperationalFinding) -> float:
    """Some findings block others."""
    blocking_ids = {
        "mission_failure",
        "trust_degradation",
        "lock_contention",
        "queue_stall",
    }
    return 70.0 if finding.finding_id in blocking_ids else 30.0


class PriorityEngine:
    """Assigns priority to findings.

    Combines multiple weighted factors into a score 0–100.
    Maps score to category CRITICAL / HIGH / MEDIUM / LOW / INFO.
    """

    def __init__(
        self,
        config: Optional[PriorityConfig] = None,
    ) -> None:
        self._config = config or _DEFAULT_CONFIG
        self._last_scores: Dict[str, PriorityScore] = {}

    @property
    def config(self) -> PriorityConfig:
        return self._config

    def prioritize(
        self,
        findings: List[OperationalFinding],
    ) -> List[PriorityScore]:
        """Assign priority to each finding.

        Returns scores sorted descending (highest priority first).
        """
        scores: List[PriorityScore] = []

        for f in findings:
            components: Dict[str, float] = {}

            # Severity
            sev_score = _severity_base(f.severity, self._config)
            components["severity"] = round(sev_score * self._config.severity_weight, 2)

            # Impact
            imp_score = _estimate_impact_score(f)
            components["impact"] = round(imp_score * self._config.impact_weight, 2)

            # Confidence
            conf_score = f.confidence * 100.0
            components["confidence"] = round(conf_score * self._config.confidence_weight, 2)

            # Trust
            trust_score = 50.0  # neutral default
            for ev in f.evidence:
                if "trust" in str(ev).lower():
                    trust_score = 30.0  # degraded trust
                    break
            components["trust"] = round(trust_score * self._config.trust_weight, 2)

            # Age (newer = higher priority)
            import time
            age_seconds = time.time() - f.timestamp
            age_score = max(0.0, 100.0 - min(age_seconds / 60.0, 100.0))
            components["age"] = round(age_score * self._config.age_weight, 2)

            # Dependency
            dep_score = _estimate_dependency_score(f)
            components["dependency"] = round(dep_score * self._config.dependency_weight, 2)

            # Resource count
            res_score = _estimate_resource_score(f)
            components["resource_count"] = round(res_score * self._config.resource_weight, 2)

            # Trend
            trend_score = _estimate_trend_score(f)
            components["trend"] = round(trend_score * self._config.trend_weight, 2)

            # Total score
            total = round(sum(components.values()), 1)

            # Category
            if total >= self._config.critical_threshold:
                cat = PriorityCategory.CRITICAL
            elif total >= self._config.high_threshold:
                cat = PriorityCategory.HIGH
            elif total >= self._config.medium_threshold:
                cat = PriorityCategory.MEDIUM
            elif total >= self._config.low_threshold:
                cat = PriorityCategory.LOW
            else:
                cat = PriorityCategory.INFO

            scores.append(PriorityScore(
                finding_id=f.finding_id,
                score=total,
                category=cat,
                components=components,
            ))

        # Sort descending by score
        scores.sort(key=lambda s: s.score, reverse=True)
        self._last_scores = {s.finding_id: s for s in scores}
        return scores

    def get_score(self, finding_id: str) -> Optional[PriorityScore]:
        return self._last_scores.get(finding_id)


# ── Convenience ───────────────────────────────────────────────────────


def prioritize(
    findings: List[OperationalFinding],
) -> List[PriorityScore]:
    """One-shot: prioritize findings."""
    return PriorityEngine().prioritize(findings)


def build_rec_for_priority(
    finding: OperationalFinding,
    score: PriorityScore,
) -> str:
    """Build a recommended action label based on priority."""
    if score.category == PriorityCategory.CRITICAL:
        return "Immediate escalation recommended"
    if score.category == PriorityCategory.HIGH:
        return "Prioritize for next action"
    if score.category == PriorityCategory.MEDIUM:
        return "Schedule for review"
    if score.category == PriorityCategory.LOW:
        return "Monitor and revisit"
    return "Informational — no action required"
