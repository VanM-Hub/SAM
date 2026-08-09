"""Recovery Compliance - WP-19 (MISSION-4.5 / IP-4.5-002).

Memastikan Autonomous Recovery mematuhi Foundation & Governance: eksekusi
hanya dengan approval (Article V), tidak ada bypass, tidak ada authority
leakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .autonomous_compliance import (
    AuthorityLeakageVerification,
    ForbiddenPatternCheck,
)


@dataclass(frozen=True)
class RecoveryComplianceResult:
    """Hasil compliance recovery."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class RecoveryComplianceChecker:
    """Checker compliance untuk Autonomous Recovery."""

    def check(
        self,
        *,
        approval_before_execution: bool = True,
        authority_leakage: bool = False,
        source: str = "",
    ) -> RecoveryComplianceResult:
        checks: List[Dict[str, Any]] = [
            {
                "code": "APPROVAL_BEFORE_EXECUTION",
                "passed": approval_before_execution,
            },
            AuthorityLeakageVerification.verify(
                authority_leakage=authority_leakage
            ).as_dict(),
            ForbiddenPatternCheck.check(source).as_dict(),
        ]
        passed = all(c["passed"] for c in checks)
        return RecoveryComplianceResult(passed=passed, checks=tuple(checks))

    def certify(
        self,
        *,
        approval_before_execution: bool = True,
        authority_leakage: bool = False,
        source: str = "",
    ) -> Dict[str, Any]:
        result = self.check(
            approval_before_execution=approval_before_execution,
            authority_leakage=authority_leakage,
            source=source,
        )
        return {
            "component": "autonomous_recovery",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
