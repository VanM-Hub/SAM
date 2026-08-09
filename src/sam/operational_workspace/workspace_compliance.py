"""Workspace Compliance - WP-09 (MISSION-4.6 / IP-4.6-001).

Memastikan Workspace mematuhi Foundation & Governance: workspace tidak
melakukan Governance, Execution, tidak memiliki authority, dan tidak
melakukan Runtime mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


FORBIDDEN_PATTERNS = (
    "governance.",
    ".approve(",
    ".execute(",
    "grant_privilege",
    "os.system",
    "subprocess",
    "mutate(",
)


@dataclass(frozen=True)
class WorkspaceComplianceCheck:
    """Satu check compliance workspace."""

    code: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"code": self.code, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class WorkspaceComplianceResult:
    """Hasil compliance workspace."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class GovernanceBoundaryCheck:
    """Verifikasi workspace tidak melakukan governance/execution."""

    @staticmethod
    def verify(
        *,
        governance: bool = False,
        execution: bool = False,
        authority: bool = False,
        runtime_mutation: bool = False,
    ) -> WorkspaceComplianceCheck:
        passed = not (governance or execution or authority or runtime_mutation)
        return WorkspaceComplianceCheck(
            "NO_GOVERNANCE_ACTION", passed, "ok" if passed else "forbidden action"
        )


class ApiDependencyVerification:
    """Verifikasi workspace hanya mengonsumsi capability via API."""

    @staticmethod
    def verify(api_only: bool = True) -> WorkspaceComplianceCheck:
        return WorkspaceComplianceCheck(
            "API_ONLY", api_only, "ok" if api_only else "direct domain access"
        )


class ForbiddenPatternCheck:
    """Deteksi pola terlarang dalam source workspace."""

    @staticmethod
    def check(source: str = "") -> WorkspaceComplianceCheck:
        if not source:
            return WorkspaceComplianceCheck("FORBIDDEN", True, "no source")
        found = [p for p in FORBIDDEN_PATTERNS if p in source]
        return WorkspaceComplianceCheck(
            "FORBIDDEN", not found, "; ".join(found) if found else "clean"
        )


class WorkspaceComplianceChecker:
    """Checker compliance untuk workspace."""

    def certify(
        self,
        *,
        source: str = "",
        governance: bool = False,
        execution: bool = False,
        authority: bool = False,
        runtime_mutation: bool = False,
        api_only: bool = True,
    ) -> Dict[str, Any]:
        checks = (
            GovernanceBoundaryCheck.verify(
                governance=governance,
                execution=execution,
                authority=authority,
                runtime_mutation=runtime_mutation,
            ),
            ApiDependencyVerification.verify(api_only=api_only),
            ForbiddenPatternCheck.check(source),
        )
        passed = all(c.passed for c in checks)
        return {
            "component": "operational_workspace",
            "passed": passed,
            "certified": passed,
            "checks": [c.as_dict() for c in checks],
        }
