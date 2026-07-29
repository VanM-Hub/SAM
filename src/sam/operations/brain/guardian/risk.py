"""
OP-343 — Guardian Risk Assessment

Hitung 6 dimensi risk:
  1. Operational Risk
  2. Policy Risk
  3. Execution Risk
  4. Dependency Risk
  5. Approval Risk
  6. Confidence Risk

Output immutable DTO. Rule-based. Synchronous.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class RiskLevel(str, Enum):
    """Tingkat risk."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass(frozen=True)
class RiskDimension:
    """Skor dan level satu dimensi risk."""
    dimension: str
    level: RiskLevel
    score: float  # 0.0 (no risk) - 1.0 (max risk)
    factors: Tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    @property
    def is_significant(self) -> bool:
        return self.level in (RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "level": self.level.value,
            "score": self.score,
            "is_significant": self.is_significant,
            "factors": list(self.factors),
            "description": self.description,
        }


@dataclass(frozen=True)
class RiskAssessment:
    """Hasil assessment risk lengkap."""
    assessment_id: str
    overall_level: RiskLevel
    dimensions: Tuple[RiskDimension, ...] = field(default_factory=tuple)
    overall_score: float = 0.0
    summary: str = ""
    top_risks: Tuple[str, ...] = field(default_factory=tuple)
    mitigations: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_safe(self) -> bool:
        return self.overall_level in (RiskLevel.NONE, RiskLevel.LOW)

    @property
    def dimension_count(self) -> int:
        return len(self.dimensions)

    @property
    def significant_risks(self) -> List[RiskDimension]:
        return [d for d in self.dimensions if d.is_significant]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "overall_level": self.overall_level.value,
            "overall_score": self.overall_score,
            "is_safe": self.is_safe,
            "dimensions": [d.dimension for d in self.dimensions],
            "top_risks": list(self.top_risks),
            "summary": self.summary,
        }


class GuardianRiskAssessment:
    """Risk assessment 6 dimensi. Rule-based. Synchronous."""

    DIMENSIONS = [
        "operational", "policy", "execution",
        "dependency", "approval", "confidence",
    ]

    def __init__(self) -> None:
        self._assessment_count = 0

    @property
    def assessment_count(self) -> int:
        return self._assessment_count

    @staticmethod
    def _score_to_level(score: float) -> RiskLevel:
        if score <= 0.1:
            return RiskLevel.NONE
        elif score <= 0.3:
            return RiskLevel.LOW
        elif score <= 0.6:
            return RiskLevel.MEDIUM
        elif score <= 0.85:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def assess(
        self,
        system_health: str = "healthy",
        health_score: float = 1.0,
        policy_violations: int = 0,
        policy_score: float = 1.0,
        execution_complexity: str = "low",
        execution_failures: int = 0,
        dependency_pending: int = 0,
        dependency_count: int = 0,
        dependency_risk: str = "low",
        approval_missing: int = 0,
        approval_required: int = 0,
        approval_stale: int = 0,
        confidence_score: float = 1.0,
        evidence_quality: float = 1.0,
        assessment_id: Optional[str] = None,
        **kwargs: Any,
    ) -> RiskAssessment:
        """Assess 6 dimensi risk.

        Returns:
            RiskAssessment immutable.
        """
        import uuid
        aid = assessment_id or f"ra-{uuid.uuid4().hex[:8]}"
        self._assessment_count += 1
        dims: List[RiskDimension] = []
        mitigations: List[str] = []

        # 1. Operational Risk
        op_factors: list = []
        if system_health == "critical":
            op_score = 0.9
            op_factors.append("Kritis: system health critical")
            mitigations.append("Perbaiki system health sebelum eksekusi")
        elif system_health == "degraded":
            op_score = 0.5
            op_factors.append("Waspada: system degraded")
            mitigations.append("Monitor system health selama eksekusi")
        else:
            op_score = max(0.1, 1.0 - health_score)

        dims.append(RiskDimension(
            dimension="operational", level=self._score_to_level(op_score),
            score=op_score, factors=tuple(op_factors),
            description=f"System: {system_health}, score: {health_score:.2f}",
        ))

        # 2. Policy Risk
        pol_factors: list = []
        pol_score = min(1.0, policy_violations * 0.25 + (1.0 - policy_score))
        if policy_violations > 0:
            pol_factors.append(f"{policy_violations} policy violation(s)")
        if pol_score > 0.5:
            mitigations.append("Resolve policy violations")
        dims.append(RiskDimension(
            dimension="policy", level=self._score_to_level(pol_score),
            score=pol_score, factors=tuple(pol_factors),
            description=f"{policy_violations} violations, score: {policy_score:.2f}",
        ))

        # 3. Execution Risk
        ex_factors: list = []
        complexity_map = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
        ex_score = complexity_map.get(execution_complexity, 0.5)
        if execution_failures > 0:
            ex_score = min(1.0, ex_score + execution_failures * 0.2)
            ex_factors.append(f"{execution_failures} previous failure(s)")
        if ex_score > 0.5:
            mitigations.append(f"Execution complexity {execution_complexity}")
        dims.append(RiskDimension(
            dimension="execution", level=self._score_to_level(ex_score),
            score=ex_score, factors=tuple(ex_factors),
            description=f"Complexity: {execution_complexity}, failures: {execution_failures}",
        ))

        # 4. Dependency Risk
        dep_factors: list = []
        dep_score = 0.0
        if dependency_count > 0:
            dep_score = min(1.0, dependency_pending / max(1, dependency_count))
        if dependency_risk == "high":
            dep_score = max(dep_score, 0.6)
            dep_factors.append("High dependency risk")
        if dependency_pending > 0:
            dep_factors.append(f"{dependency_pending} pending")
        if dep_score > 0.4:
            mitigations.append("Complete pending dependencies")
        dims.append(RiskDimension(
            dimension="dependency", level=self._score_to_level(dep_score),
            score=dep_score, factors=tuple(dep_factors),
            description=f"{dependency_pending}/{dependency_count} pending",
        ))

        # 5. Approval Risk
        app_factors: list = []
        if approval_required > 0:
            app_score = min(1.0, (approval_missing + approval_stale) / approval_required)
        else:
            app_score = 0.0
        if approval_missing > 0:
            app_factors.append(f"{approval_missing} missing")
        if approval_stale > 0:
            app_factors.append(f"{approval_stale} stale")
        if app_score > 0.3:
            mitigations.append("Obtain missing approvals")
        dims.append(RiskDimension(
            dimension="approval", level=self._score_to_level(app_score),
            score=app_score, factors=tuple(app_factors),
            description=f"{approval_missing} missing, {approval_stale} stale",
        ))

        # 6. Confidence Risk
        conf_factors: list = []
        conf_score = 1.0 - min(1.0, confidence_score * evidence_quality)
        if confidence_score < 0.7:
            conf_factors.append(f"Low confidence: {confidence_score:.2f}")
        if evidence_quality < 0.5:
            conf_factors.append(f"Low evidence quality: {evidence_quality:.2f}")
        if conf_score > 0.4:
            mitigations.append("Improve confidence/evidence quality")
        dims.append(RiskDimension(
            dimension="confidence", level=self._score_to_level(conf_score),
            score=conf_score, factors=tuple(conf_factors),
            description=f"Confidence: {confidence_score:.2f}, evidence: {evidence_quality:.2f}",
        ))

        # Overall — weighted: worst dimension dominates
        overall_score = sum(d.score for d in dims) / len(dims) if dims else 0.0
        worst_dim = max(dims, key=lambda d: d.score) if dims else None
        worst_score = worst_dim.score if worst_dim else 0.0
        # Final score = blend of average and worst (60% worst, 40% avg)
        blended_score = worst_score * 0.6 + overall_score * 0.4
        overall_level = self._score_to_level(blended_score)
        significant = [d for d in dims if d.is_significant]

        if overall_level == RiskLevel.NONE:
            summary = "Tidak ada risk signifikan"
        elif overall_level == RiskLevel.LOW:
            summary = "Risk rendah — aman dijalankan"
        elif overall_level == RiskLevel.MEDIUM:
            summary = "Risk medium — perlu monitoring"
        elif overall_level == RiskLevel.HIGH:
            dim_names = [d.dimension for d in significant]
            summary = f"Risk tinggi pada: {', '.join(dim_names)}"
        else:
            dim_names = [d.dimension for d in significant]
            summary = f"Risk kritis pada: {', '.join(dim_names)}"

        return RiskAssessment(
            assessment_id=aid,
            overall_level=overall_level,
            dimensions=tuple(dims),
            overall_score=overall_score,
            summary=summary,
            top_risks=tuple(d.dimension for d in significant),
            mitigations=tuple(mitigations),
        )
