"""Recovery Verification - WP-14 (MISSION-4.5 / IP-4.5-002).

Memverifikasi hasil pemulihan (read-only, evidence-based).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .recovery_execution import RecoverySession


@dataclass(frozen=True)
class RecoveryVerificationResult:
    """Hasil verifikasi pemulihan."""

    session_id: str
    verified: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "verified": self.verified,
            "checks": list(self.checks),
        }


class RecoveryVerifier:
    """Verifier hasil pemulihan."""

    @staticmethod
    def verify(
        session: RecoverySession,
        *,
        all_executed: bool = True,
        no_failures: bool = True,
    ) -> RecoveryVerificationResult:
        executed = session.executed
        checks = [
            {
                "code": "COMPLETED",
                "passed": session.status == "completed",
            },
            {
                "code": "ALL_STEPS_EXECUTED",
                "passed": all(s.status == "executed" for s in executed) if executed else all_executed,
            },
            {
                "code": "NO_FAILURES",
                "passed": not any(s.status == "failed" for s in executed) if executed else no_failures,
            },
        ]
        verified = all(c["passed"] for c in checks)
        return RecoveryVerificationResult(
            session_id=session.session_id,
            verified=verified,
            checks=tuple(checks),
        )


class SelfDebugging:
    """Self-diagnostic (read-only) - menghasilkan evidence untuk debugging."""

    @staticmethod
    def inspect(state: Dict[str, Any]) -> Dict[str, Any]:
        findings = []
        for key, value in state.items():
            text = str(value).lower()
            if "fail" in text or "error" in text or "critical" in text:
                findings.append(
                    {"component": key, "issue": str(value), "severity": "high"}
                )
        return {
            "inspected_count": len(state),
            "findings": findings,
            "clean": not findings,
        }
