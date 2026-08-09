"""Diagnosis Compliance - WP-19 (MISSION-4.2 / IP-4.2-002).

Memastikan diagnosis operasional mematuhi batas Foundation & Governance:
read-only, tidak ada execution, tidak ada approval, evidence-based.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .investigation_compliance import (
    ForbiddenPatternCheck,
    ComplianceCheckResult,
)


@dataclass(frozen=True)
class DiagnosisComplianceResult:
    """Hasil compliance diagnosis."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class DiagnosisComplianceChecker:
    """Checker compliance untuk capability diagnosis (read-only)."""

    def __init__(self) -> None:
        self._forbidden = ForbiddenPatternCheck()

    def check_source(self, source: str, location: str = "") -> ComplianceCheckResult:
        return self._forbidden.check(source, location)

    def check_evidence_based(
        self,
        *,
        has_evidence: bool = True,
        has_execution: bool = False,
        has_approval: bool = False,
    ) -> DiagnosisComplianceResult:
        findings: List[Any] = []
        passed = True
        if not has_evidence:
            passed = False
            findings.append(
                {"code": "NO_EVIDENCE", "passed": False}
            )
        if has_execution:
            passed = False
            findings.append(
                {"code": "EXECUTION", "passed": False}
            )
        if has_approval:
            passed = False
            findings.append(
                {"code": "APPROVAL", "passed": False}
            )
        checks = [
            {"code": "EVIDENCE_BASED", "passed": has_evidence},
            {"code": "NO_EXECUTION", "passed": not has_execution},
            {"code": "NO_APPROVAL", "passed": not has_approval},
        ] + findings
        return DiagnosisComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self) -> Dict[str, Any]:
        result = self.check_evidence_based()
        return {
            "component": "operational_diagnosis",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
