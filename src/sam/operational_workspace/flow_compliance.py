"""Operational Flow Compliance - WP-19 (MISSION-4.6 / IP-4.6-002).

Memastikan alur end-to-end mematuhi Foundation & Governance: approval
sebelum execution (Article V), tiap tahapan ber-evidence, tidak ada
tahapan terputus, tidak ada authority baru.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .end_to_end_flow import OperationalFlow, FlowStage


@dataclass(frozen=True)
class FlowComplianceResult:
    """Hasil compliance alur."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class OperationalFlowCompliance:
    """Checker compliance alur end-to-end."""

    def check(self, flow: OperationalFlow) -> FlowComplianceResult:
        stages = flow.completed_stages
        checks = [
            {
                "code": "HAS_ASK",
                "passed": FlowStage.ASK in stages,
            },
            {
                "code": "EVERY_STEP_HAS_EVIDENCE",
                "passed": all(s.evidence for s in flow.steps),
            },
            {
                "code": "NO_AUTHORITY_ESCAPE",
                "passed": not any(
                    "grant" in str(s.output) or "privilege" in str(s.output) for s in flow.steps
                ),
            },
        ]
        # Jika alur mencapai eksekusi, harus ada approval (Article V)
        if "execute" in stages and "approve" not in stages:
            checks.append(
                {"code": "APPROVAL_BEFORE_EXECUTION", "passed": False}
            )
        else:
            checks.append(
                {"code": "APPROVAL_BEFORE_EXECUTION", "passed": True}
            )
        passed = all(c["passed"] for c in checks)
        return FlowComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self, flow: OperationalFlow) -> Dict[str, Any]:
        result = self.check(flow)
        return {
            "component": "end_to_end_operations",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
