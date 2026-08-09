"""Autonomous Compliance - WP-09 (MISSION-4.5 / IP-4.5-001).

Memastikan Autonomous operations mematuhi Foundation & Governance: tidak ada
runtime mutation, execution, approval bypass, atau authority leakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


FORBIDDEN_PATTERNS = (
    ".execute(",
    ".approve(",
    "bypass_approval",
    "grant_privilege",
    "os.system",
    "subprocess.run",
)


@dataclass(frozen=True)
class AutonomousComplianceCheck:
    """Hasil pengecekan compliance."""

    code: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"code": self.code, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class AutonomousComplianceResult:
    """Hasil compliance (kumpulan check)."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class ReadOnlyVerification:
    """Verifikasi read-only (tanpa mutation/execution)."""

    @staticmethod
    def verify(
        *,
        runtime_mutation: bool = False,
        execution: bool = False,
        approval_bypass: bool = False,
    ) -> AutonomousComplianceCheck:
        passed = not (runtime_mutation or execution or approval_bypass)
        detail = "ok" if passed else {
            "runtime_mutation" if runtime_mutation else None,
            "execution" if execution else None,
            "approval_bypass" if approval_bypass else None,
        }
        return AutonomousComplianceCheck("READ_ONLY", passed, str(detail))


class AuthorityLeakageVerification:
    """Verifikasi tidak ada authority leakage."""

    @staticmethod
    def verify(authority_leakage: bool = False) -> AutonomousComplianceCheck:
        return AutonomousComplianceCheck(
            "NO_AUTHORITY_LEAKAGE", not authority_leakage, "ok" if not authority_leakage else "leakage"
        )


class ForbiddenPatternCheck:
    """Deteksi pola terlarang dalam source."""

    @staticmethod
    def check(source: str = "") -> AutonomousComplianceCheck:
        if not source:
            return AutonomousComplianceCheck("FORBIDDEN", True, "no source")
        found = [p for p in FORBIDDEN_PATTERNS if p in source]
        return AutonomousComplianceCheck(
            "FORBIDDEN", not found, "; ".join(found) if found else "clean"
        )


class AutonomousComplianceChecker:
    """Checker compliance terpadu untuk Autonomous Operations."""

    def certify(
        self,
        *,
        source: str = "",
        runtime_mutation: bool = False,
        execution: bool = False,
        approval_bypass: bool = False,
        authority_leakage: bool = False,
    ) -> Dict[str, Any]:
        checks = (
            ReadOnlyVerification.verify(
                runtime_mutation=runtime_mutation,
                execution=execution,
                approval_bypass=approval_bypass,
            ),
            AuthorityLeakageVerification.verify(authority_leakage=authority_leakage),
            ForbiddenPatternCheck.check(source),
        )
        passed = all(c.passed for c in checks)
        return {
            "component": "autonomous_operations",
            "passed": passed,
            "certified": passed,
            "checks": [c.as_dict() for c in checks],
        }
