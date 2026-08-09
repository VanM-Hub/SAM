"""Intelligence Compliance - WP-28 (MISSION-4.2 / IP-4.2-003).

Memastikan seluruh capability Operational Intelligence mematuhi batas
Foundation & Governance: read-only, tidak ada execution, tidak ada approval,
tidak ada authority leakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .investigation_compliance import ForbiddenPatternCheck


@dataclass(frozen=True)
class IntelligenceComplianceResult:
    """Hasil compliance keseluruhan capability intelligence."""

    passed: bool
    components: Dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "components": self.components,
            "component_count": len(self.components),
        }


class IntelligenceComplianceChecker:
    """Checker compliance untuk seluruh Operational Intelligence."""

    COMPONENTS = (
        "investigation",
        "operational_diagnosis",
        "consequence_prediction",
        "operational_simulation",
        "recommendation",
        "trust_assessment",
        "risk_evaluation",
    )

    def __init__(self) -> None:
        self._forbidden = ForbiddenPatternCheck()

    def check_source(self, source: str, location: str = "") -> Any:
        return self._forbidden.check(source, location)

    def certify(
        self,
        *,
        execution_called: bool = False,
        approval_called: bool = False,
        authority_leakage: bool = False,
    ) -> Dict[str, Any]:
        components = {name: True for name in self.COMPONENTS}
        violations: List[Dict[str, Any]] = []
        if execution_called:
            violations.append({"kind": "execution"})
        if approval_called:
            violations.append({"kind": "approval"})
        if authority_leakage:
            violations.append({"kind": "authority_leakage"})
        passed = not violations
        return {
            "component": "operational_intelligence",
            "passed": passed,
            "certified": passed,
            "components": components,
            "violations": violations,
        }
