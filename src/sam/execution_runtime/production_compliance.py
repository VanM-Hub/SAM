"""Production Compliance - IP-4.1-003 WP-28.

Production Execution.
Memastikan jalur execution produksi mematuhi Foundation menyeluruh.

Scope (Foundation immutable):
- Tidak ada execution produksi tanpa approval (Article V).
- Tidak ada authority leakage / bypass (Article XII).
- Retry/timeout tidak menyimpang dari governance.
- Multi-provider tetap provider-agnostic & deterministik (Article VII/VIII).

Mengagregasi compliance jalur eksekusi + invariant produksi. Read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .execution_compliance import ExecutionCompliance, ExecutionComplianceChecker


# Pola yang dilarang di lapisan produksi (authority/bypass/multi-provider bypass)
_PRODUCTION_FORBIDDEN = (
    "grant_privilege",
    "bypass_approval",
    "execute_without_approval",
    "self_authorize",
    "escalate_privilege",
    "auto_approve",
)


@dataclass(frozen=True)
class ProductionCompliance:
    """Hasil compliance produksi (immutable)."""

    subject: str
    passed: bool
    execution_compliance: ExecutionCompliance
    checks: Tuple[str, ...] = field(default_factory=tuple)
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "subject": self.subject,
            "passed": self.passed,
            "execution_compliance": self.execution_compliance.as_dict(),
            "checks": list(self.checks),
            "detail": self.detail,
        }


class ProductionComplianceChecker:
    """Checker compliance jalur produksi (read-only)."""

    def __init__(self, forbidden: Tuple[str, ...] = _PRODUCTION_FORBIDDEN) -> None:
        self._forbidden = forbidden
        self._execution_checker = ExecutionComplianceChecker(forbidden=forbidden)

    def check(
        self,
        subject: str,
        source_blocks: Optional[List[str]] = None,
        requests: Optional[List] = None,
    ) -> ProductionCompliance:
        """Compliance produksi: gabungan execution compliance + invariant retry.

        Invariant produksi yang ditambahkan:
        - Approval tetap prasyarat (dari execution compliance).
        - Tidak ada auto-approve (scan forbidden).
        """
        execution_result = self._execution_checker.check(
            subject=subject, source_blocks=source_blocks, requests=requests)
        checks: list = []

        # Production guardrail tambahan (deskriptif, deterministik)
        if source_blocks:
            detection = self._scan_production_forbidden(source_blocks)
            checks.append("no_auto_approve by scan" if not detection else
                          "AUTO_APPROVE_DETECTED: {}".format(detection))

        passed = execution_result.passed and all(
            c.startswith("no_") for c in checks) if checks else execution_result.passed

        return ProductionCompliance(
            subject=subject,
            passed=bool(passed),
            execution_compliance=execution_result,
            checks=tuple(checks),
            detail="" if bool(passed) else "production compliance gagal",
        )

    def _scan_production_forbidden(self, source_blocks: List[str]) -> List[str]:
        """Deteksi pola production-forbidden (auto-approve/dll) di source."""
        findings: List[str] = []
        for block in source_blocks:
            for i, line in enumerate(block.splitlines(), 1):
                if self._is_implementation(line):
                    for pattern in self._forbidden:
                        if pattern in line and ("(" in line or "=" in line):
                            findings.append("{}:{}".format(pattern, i))
        return findings

    def _is_implementation(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or '"""' in stripped or "'''" in stripped:
            return False
        lower = stripped.lower()
        if any(x in lower for x in ("menjelaskan", "dilarang", "tidak boleh",
                                     "must not", "should not")):
            return False
        return True
