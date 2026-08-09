"""Universal Workflow Certification - WP-41..50 (MISSION-5.4 / IP-5.4-005).

Rangkaian sertifikasi workflow: foundation, composition, execution, state &
recovery, governance, determinism, failure, audit, regression, mission.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple


class WorkflowCertStatus(str, Enum):
    """Status certification workflow."""

    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class WorkflowCertEvidence:
    """Bukti certification workflow."""

    name: str
    passed: bool

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed}


class WorkflowCertification:
    """Sertifikasi Workflow (WP-41..50)."""

    def __init__(self) -> None:
        self._evidences: list = []

    def _add(self, name: str, flags: list) -> None:
        for idx, passed in enumerate(flags):
            self._evidences.append(WorkflowCertEvidence(name=f"{name}#{idx + 1}", passed=bool(passed)))

    def foundation_certification(self, *, validated=True, persistent=True) -> None:
        self._add("workflow_foundation", [validated, persistent])

    def composition_certification(self, *, composed=True, dependency_resolved=True) -> None:
        self._add("workflow_composition", [composed, dependency_resolved])

    def execution_certification(self, *, approved=True, verified=True) -> None:
        self._add("workflow_execution", [approved, verified])

    def state_recovery_certification(self, *, deterministic=True, recoverable=True) -> None:
        self._add("workflow_state_recovery", [deterministic, recoverable])

    def governance_certification(self, *, no_authority=True, governed=True) -> None:
        self._add("workflow_governance", [no_authority, governed])

    def determinism_certification(self, *, deterministic=True, idempotent=True) -> None:
        self._add("workflow_determinism", [deterministic, idempotent])

    def failure_certification(self, *, handled=True, propagated=True) -> None:
        self._add("workflow_failure", [handled, propagated])

    def audit_certification(self, *, traceable=True, explainable=True) -> None:
        self._add("workflow_audit", [traceable, explainable])

    def regression_compliance(self, *, regression=True, compliance=True) -> None:
        self._add("workflow_regression", [regression, compliance])

    def mission_certification(self, *, integrated=True, architecture_accepted=True) -> None:
        self._add("workflow_mission", [integrated, architecture_accepted])

    def certify(self) -> Dict[str, Any]:
        total = len(self._evidences)
        passed = sum(1 for e in self._evidences if e.passed)
        if total == 0:
            status = WorkflowCertStatus.INSUFFICIENT_EVIDENCE
        elif passed == total:
            status = WorkflowCertStatus.CERTIFIED
        elif passed >= max(1, total - 2):
            status = WorkflowCertStatus.CONDITIONALLY_CERTIFIED
        else:
            status = WorkflowCertStatus.NOT_CERTIFIED
        return {
            "component": "universal_workflow.mission_5_4",
            "passed": status == WorkflowCertStatus.CERTIFIED,
            "certified": status == WorkflowCertStatus.CERTIFIED,
            "status": status.value,
            "passed_count": passed,
            "total_count": total,
        }


@dataclass(frozen=True)
class WorkflowComplianceResult:
    """Hasil compliance workflow (re-export agregat)."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)


class WorkflowComplianceChecker:
    """Checker compliance agregat workflow."""

    def check(self, *, foundation=True, composition=True, execution=True, recovery=True, governance=True, audited=True) -> WorkflowComplianceResult:
        checks = [
            {"code": "FOUNDATION", "passed": foundation},
            {"code": "COMPOSITION", "passed": composition},
            {"code": "EXECUTION", "passed": execution},
            {"code": "RECOVERY", "passed": recovery},
            {"code": "GOVERNANCE", "passed": governance},
            {"code": "AUDITED", "passed": audited},
        ]
        return WorkflowComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(**kwargs)
        return {"component": "universal_workflow", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
