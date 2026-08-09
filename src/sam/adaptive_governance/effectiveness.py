"""Adaptive Governance - Effectiveness Intelligence - WP-11..20 (MISSION-5.6).

Governance effectiveness model, policy/workflow/execution outcome analysis,
failure pattern analysis, risk analysis, effectiveness recommendation,
explainability, compliance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple


class RiskLevel(str, Enum):
    """Level risiko governance."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class EffectivenessMetric:
    """Metrik efektivitas."""

    name: str
    value: float
    healthy: bool

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "healthy": self.healthy}


@dataclass(frozen=True)
class EffectivenessReport:
    """Laporan efektivitas governance."""

    scope: str
    metrics: Tuple[EffectivenessMetric, ...] = field(default_factory=tuple)

    @property
    def overall_healthy(self) -> bool:
        return bool(self.metrics) and all(m.healthy for m in self.metrics)

    def as_dict(self) -> dict:
        return {
            "scope": self.scope,
            "metrics": [m.as_dict() for m in self.metrics],
            "overall_healthy": self.overall_healthy,
        }


class EffectivenessAnalyzer:
    """Menganalisis efektivitas governance."""

    def analyze(self, scope: str, success_rate: float = 1.0) -> EffectivenessReport:
        return EffectivenessReport(
            scope=scope,
            metrics=(
                EffectivenessMetric("policy_effectiveness", success_rate, success_rate >= 0.8),
                EffectivenessMetric("workflow_effectiveness", success_rate, success_rate >= 0.8),
                EffectivenessMetric("execution_outcome", success_rate, success_rate >= 0.8),
            ),
        )


@dataclass(frozen=True)
class FailurePattern:
    """Pola kegagalan."""

    pattern: str
    frequency: int

    def as_dict(self) -> dict:
        return {"pattern": self.pattern, "frequency": self.frequency}


class FailurePatternAnalyzer:
    """Menganalisis pola kegagalan."""

    def analyze(self, failures: Tuple[str, ...]) -> Tuple[FailurePattern, ...]:
        counts: dict = {}
        for f in failures:
            counts[f] = counts.get(f, 0) + 1
        return tuple(FailurePattern(k, v) for k, v in sorted(counts.items(), key=lambda i: -i[1]))


class GovernanceRisk:
    """Risiko governance."""

    def __init__(self, risk_id: str, description: str, level: RiskLevel = RiskLevel.MEDIUM) -> None:
        self.risk_id = risk_id
        self.description = description
        self.level = level

    def as_dict(self) -> dict:
        return {"risk_id": self.risk_id, "description": self.description, "level": self.level.value}


class RiskAnalyzer:
    """Menganalisis risiko governance."""

    def analyze(self, failure_rate: float = 0.0) -> GovernanceRisk:
        if failure_rate >= 0.5:
            level = RiskLevel.CRITICAL
        elif failure_rate >= 0.3:
            level = RiskLevel.HIGH
        elif failure_rate >= 0.15:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return GovernanceRisk("risk-1", f"failure_rate={round(failure_rate, 3)}", level)


@dataclass(frozen=True)
class EffectivenessRecommendation:
    """Rekomendasi efektivitas (usulan, tidak auto-apply)."""

    scope: str
    suggestion: str
    evidence_based: bool = True

    def as_dict(self) -> dict:
        return {"scope": self.scope, "suggestion": self.suggestion, "evidence_based": self.evidence_based}


class EffectivenessRecommender:
    """Menyusun rekomendasi efektivitas."""

    def recommend(self, report: EffectivenessReport) -> EffectivenessRecommendation:
        suggestion = "maintain current governance" if report.overall_healthy else "propose evaluation of underperforming domain"
        return EffectivenessRecommendation(report.scope, suggestion)


class EffectivenessExplainability:
    """Menjelaskan analisis efektivitas."""

    def explain(self, report: EffectivenessReport) -> Dict[str, Any]:
        return {"scope": report.scope, "metrics": [m.as_dict() for m in report.metrics], "overall_healthy": report.overall_healthy, "explainable": True}


class EffectivenessComplianceChecker:
    """Checker compliance analisis efektivitas."""

    def check(self, *, analyze_only=True, evidence_based=True, no_auto_apply=True, no_authority_change=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "ANALYZE_ONLY", "passed": analyze_only},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "NO_AUTO_APPLY", "passed": no_auto_apply},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.effectiveness", "passed": passed, "certified": passed, "checks": [c for c in checks]}
