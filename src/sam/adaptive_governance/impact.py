"""Adaptive Governance - Impact Assessment - WP-31..40 (MISSION-5.6).

Impact model untuk menilai dampak perubahan governance pada Citizen
(Provider, Agent, Tool, Workflow, Enterprise) dan runtime. Evaluative, tidak
mengubah governance.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class ImpactTarget(str, Enum):
    """Target dampak."""

    CITIZEN = "citizen"
    RUNTIME = "runtime"
    PROVIDER = "provider"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    ENTERPRISE = "enterprise"


class ImpactSeverity(str, Enum):
    """Tingkat dampak."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ImpactAssessment:
    """Hasil penilaian dampak."""

    target: ImpactTarget
    target_id: str
    severity: ImpactSeverity
    description: str = ""

    @property
    def acceptable(self) -> bool:
        return self.severity in (ImpactSeverity.NONE, ImpactSeverity.LOW)

    def as_dict(self) -> dict:
        return {
            "target": self.target.value,
            "target_id": self.target_id,
            "severity": self.severity.value,
            "description": self.description,
            "acceptable": self.acceptable,
        }


class ImpactAnalyzer:
    """Menganalisis dampak perubahan pada sebuah target."""

    def analyze(self, target: ImpactTarget, target_id: str, *, severity: ImpactSeverity = ImpactSeverity.LOW, description: str = "") -> ImpactAssessment:
        return ImpactAssessment(target, target_id, severity, description or f"impact on {target.value}:{target_id}")


class ImpactComplianceChecker:
    """Checker compliance penilaian dampak."""

    def check(self, *, assess_only=True, no_authority_change=True, evidence_based=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "ASSESS_ONLY", "passed": assess_only},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.impact", "passed": passed, "certified": passed, "checks": [c for c in checks]}
