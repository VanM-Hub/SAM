"""Knowledge Compliance - WP-19 (MISSION-4.3 / IP-4.3-002).

Memastikan Operational Knowledge mematuhi Foundation & Governance:
setiap knowledge memiliki evidence, tidak ada authority leakage, tidak ada
mutation terhadap governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class KnowledgeComplianceResult:
    """Hasil compliance knowledge."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class KnowledgeComplianceChecker:
    """Checker compliance untuk Operational Knowledge."""

    def check(
        self,
        *,
        all_have_evidence: bool = True,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
    ) -> KnowledgeComplianceResult:
        checks = [
            {"code": "EVIDENCE_BASED", "passed": all_have_evidence},
            {"code": "NO_EXECUTION", "passed": not execution},
            {"code": "NO_APPROVAL", "passed": not approval},
            {"code": "NO_GOVERNANCE_MUTATION", "passed": not governance_mutation},
        ]
        passed = all(c["passed"] for c in checks)
        return KnowledgeComplianceResult(passed=passed, checks=tuple(checks))

    def certify(
        self,
        *,
        all_have_evidence: bool = True,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
    ) -> Dict[str, Any]:
        result = self.check(
            all_have_evidence=all_have_evidence,
            execution=execution,
            approval=approval,
            governance_mutation=governance_mutation,
        )
        return {
            "component": "operational_knowledge",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
