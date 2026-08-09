"""Learning Compliance - WP-28 (MISSION-4.3 / IP-4.3-003).

Memastikan Continuous Learning mematuhi Foundation & Governance:
pembelajaran berbasis evidence, tidak ada execution/approval/authority
leakage, tidak ada mutation terhadap Governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class LearningComplianceResult:
    """Hasil compliance learning."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class LearningComplianceChecker:
    """Checker compliance untuk Continuous Learning."""

    def check(
        self,
        *,
        evidence_based: bool = True,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
        authority_leakage: bool = False,
    ) -> LearningComplianceResult:
        checks = [
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "NO_EXECUTION", "passed": not execution},
            {"code": "NO_APPROVAL", "passed": not approval},
            {"code": "NO_GOVERNANCE_MUTATION", "passed": not governance_mutation},
            {"code": "NO_AUTHORITY_LEAKAGE", "passed": not authority_leakage},
        ]
        passed = all(c["passed"] for c in checks)
        return LearningComplianceResult(passed=passed, checks=tuple(checks))

    def certify(
        self,
        *,
        evidence_based: bool = True,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
        authority_leakage: bool = False,
    ) -> Dict[str, Any]:
        result = self.check(
            evidence_based=evidence_based,
            execution=execution,
            approval=approval,
            governance_mutation=governance_mutation,
            authority_leakage=authority_leakage,
        )
        return {
            "component": "continuous_learning",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
