"""Workspace Compliance & Tool Certification - WP-39..50.

Compliance untuk workspace Tool dan certification seluruh Tool Integration.
Certification tidak memberikan authority baru.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class WorkspaceComplianceResult:
    """Hasil compliance workspace."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class WorkspaceComplianceChecker:
    """Checker compliance untuk Operational Tool Workspace."""

    def check(
        self,
        *,
        read_only: bool = True,
        no_execution: bool = True,
        no_authority: bool = True,
        no_governance_override: bool = True,
    ) -> WorkspaceComplianceResult:
        checks = [
            {"code": "READ_ONLY", "passed": read_only},
            {"code": "NO_EXECUTION", "passed": no_execution},
            {"code": "NO_AUTHORITY", "passed": no_authority},
            {"code": "NO_GOVERNANCE_OVERRIDE", "passed": no_governance_override},
        ]
        passed = all(c["passed"] for c in checks)
        return WorkspaceComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(**kwargs)
        return {
            "component": "universal_tool.workspace",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }


class ToolCertStatus(str, Enum):
    """Status certification tool."""

    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ToolCertificationEvidence:
    """Satu bukti certification tool."""

    name: str
    passed: bool

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed}


@dataclass(frozen=True)
class ToolCertificationResult:
    """Hasil certification tool."""

    status: ToolCertStatus
    passed_count: int
    total_count: int
    evidences: Tuple[ToolCertificationEvidence, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "status": self.status.value,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "evidences": [e.as_dict() for e in self.evidences],
        }


class ToolCertification:
    """Rangkaian certification Tool (WP-41..50)."""

    def __init__(self) -> None:
        self._evidences: list = []

    def _add(self, name: str, flags: list, *, invert: bool = False) -> None:
        for idx, passed in enumerate(flags):
            self._evidences.append(
                ToolCertificationEvidence(name=f"{name}#{idx + 1}", passed=bool(passed))
            )

    def contract_certification(self, *, contract=True, governed=True) -> None:
        self._add("tool_contract", [contract, governed])

    def connector_certification(self, *, connected=True, isolated=True) -> None:
        self._add("connector", [connected, isolated])

    def capability_certification(self, *, resolution=True, mapping=True) -> None:
        self._add("capability", [resolution, mapping])

    def execution_certification(self, *, governed=True, audited=True) -> None:
        self._add("execution", [governed, audited])

    def security_verification(self, *, credential_isolated=True, no_secret=True) -> None:
        self._add("security", [credential_isolated, no_secret])

    def governance_verification(self, *, no_tool_authority=True, no_override=False) -> None:
        self._add("governance", [no_tool_authority, not no_override])

    def audit_verification(self, *, trail=True, append_only=True) -> None:
        self._add("audit", [trail, append_only])

    def regression_verification(self, *, passed=True) -> None:
        self._add("regression", [passed])

    def production_readiness(self, *, ready=True) -> None:
        self._add("production", [ready])

    def mission_certification(self, *, integrated=True, architecture_accepted=True) -> None:
        self._add("mission", [integrated, architecture_accepted])

    def result(self) -> ToolCertificationResult:
        total = len(self._evidences)
        passed = sum(1 for e in self._evidences if e.passed)
        if total == 0:
            status = ToolCertStatus.INSUFFICIENT_EVIDENCE
        elif passed == total:
            status = ToolCertStatus.CERTIFIED
        elif passed >= max(1, total - 2):
            status = ToolCertStatus.CONDITIONALLY_CERTIFIED
        else:
            status = ToolCertStatus.NOT_CERTIFIED
        return ToolCertificationResult(
            status=status, passed_count=passed, total_count=total, evidences=tuple(self._evidences)
        )

    def certify(self) -> Dict[str, Any]:
        result = self.result()
        return {
            "component": "universal_tool.mission_5_2",
            "passed": result.status == ToolCertStatus.CERTIFIED,
            "certified": result.status == ToolCertStatus.CERTIFIED,
            "status": result.status.value,
            "passed_count": result.passed_count,
            "total_count": result.total_count,
            "evidences": [e.as_dict() for e in result.evidences],
        }
