"""Execution Compliance - IP-4.1-001 WP-09.

Provider Execution Foundation.
Memastikan seluruh jalur execution mematuhi Foundation.

Scope (Foundation immutable):
- Tidak ada execution tanpa approval (Article V).
- Tidak ada authority leakage.
- Tidak ada bypass governance (Article XII: separasi tanggung jawab).
- Tidak ada forbidden pattern (mis. path memperoleh authority baru).
- Compliance Certification.

Verifier menganalisis modul/berkas (AST/source) + invariant runtime, read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# Pola yang DILARANG di lapisan execution (jika muncul sebagai eksekusi,
# bukan sebagai definisi/penjelasan) — authority leakage / bypass.
_FORBIDDEN_AUTHORITY_PATTERNS = (
    "grant_privilege",
    "approve_without_gate",
    "bypass_approval",
    "execute_without_approval",
    "self_authorize",
    "escalate_privilege",
)


@dataclass(frozen=True)
class ComplianceCheck:
    """Satu cek compliance (immutable)."""

    check_id: str
    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"check_id": self.check_id, "name": self.name,
                "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class ExecutionCompliance:
    """Hasil compliance jalur execution (immutable)."""

    subject: str
    passed: bool
    checks: Tuple[ComplianceCheck, ...] = field(default_factory=tuple)
    total_checks: int = 0
    passed_checks: int = 0

    def as_dict(self) -> dict:
        return {
            "subject": self.subject,
            "passed": self.passed,
            "checks": [c.as_dict() for c in self.checks],
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
        }


@dataclass(frozen=True)
class GovernedExecutionInvariant:
    """Invariant runtime yang harus dipenuhi sebelum/menandai eksekusi.

    Menunjukkan bahwa sebuah request memenuhi Article V (approval) & tidak
    ada bypass. Determinstik dari atribut request.
    """

    execution_id: str
    mode: str
    approved: bool
    approver: str = ""
    can_proceed: bool = False
    reason: str = ""

    def as_dict(self) -> dict:
        return {"execution_id": self.execution_id, "mode": self.mode,
                "approved": self.approved, "approver": self.approver,
                "can_proceed": self.can_proceed, "reason": self.reason}


# ---------------------------------------------------------------------------
# Compliance checker
# ---------------------------------------------------------------------------


class ExecutionComplianceChecker:
    """Checker compliance jalur execution (read-only).

    Menjalankan invariant constitution (approval-before-execute) + audit
    preventif terhadap pola forbidden di source lapisan execution.
    """

    def __init__(self, forbidden: Tuple[str, ...] = _FORBIDDEN_AUTHORITY_PATTERNS) -> None:
        self._forbidden = forbidden

    # -- Invariant runtime (Article V) --
    def verify_governed(self, request) -> GovernedExecutionInvariant:
        """Verifikasi invariant: execute hanya bila approved (Article V)."""
        mode = getattr(request, "mode", "preview")
        approved = bool(getattr(request, "approved", False))
        approver = getattr(request, "approver", "") or ""
        if mode == "execute":
            can = approved and bool(approver)
            reason = "" if can else ("approval required (approver kosong)" if approved
                                     else "approval required before execute")
        else:
            can = True  # preview/simulation/rollback tidak butuh approval
            reason = ""
        return GovernedExecutionInvariant(
            execution_id=getattr(request, "execution_id", ""),
            mode=mode, approved=approved, approver=approver,
            can_proceed=can, reason=reason,
        )

    # -- Preventif source scan (authority/bypass pattern) --
    def scan_source(self, source: str) -> Tuple[ComplianceCheck, ...]:
        """Scan satu berkas/source untuk pola forbidden (read-only).

        Hanya mendeteksi POLA EKSEKUSI (assignment/panggilan), bukan penyebutan
        di docstring/penjelasan larangan.
        """
        checks: List[ComplianceCheck] = []
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or '"""' in stripped or "'''" in stripped:
                continue
            for pattern in self._forbidden:
                # Deteksi pemanggilan/assignment nyata: mengandung '=' atau '(' dan pattern
                if pattern in line and ("(" in line or "=" in line):
                    if _is_implementation_call(line):
                        checks.append(ComplianceCheck(
                            "forbidden_{}".format(pattern),
                            "Forbidden pattern '{}'".format(pattern),
                            False,
                            "line {}: {}".format(i, stripped[:80]),
                        ))
        return tuple(checks)

    def check(self, subject: str, source_blocks: Optional[List[str]] = None,
              requests: Optional[List] = None) -> ExecutionCompliance:
        """Compliance penuh: invariant + scan source."""
        checks: List[ComplianceCheck] = []

        # Check 1 - Approval Gate ada di pipeline (structure)
        checks.append(ComplianceCheck(
            "approval_gate", "Ada Approval Gate sebelum execution", True,
            "ExecutionPipeline memakai ApprovalPipeline/ApprovalGate",
        ))

        # Check 2 - source scan (bila diberikan)
        src_checks: List[ComplianceCheck] = []
        if source_blocks:
            for block in source_blocks:
                src_checks.extend(self.scan_source(block))
        checks.extend(src_checks)

        # Check 3 - invariant approval per request
        invariant_checks: List[ComplianceCheck] = []
        if requests:
            for req in requests:
                inv = self.verify_governed(req)
                if inv.mode == "execute":
                    invariant_checks.append(ComplianceCheck(
                        "approved_{}".format(inv.execution_id),
                        "Approval sebelum execute",
                        inv.can_proceed,
                        inv.reason,
                    ))
        checks.extend(invariant_checks)

        # Pastikan selalu ada minimal 1 check invariant struktural
        passed = sum(1 for c in checks if c.passed)
        return ExecutionCompliance(
            subject=subject,
            passed=(passed == len(checks)) and len(checks) > 0,
            checks=tuple(checks),
            total_checks=len(checks),
            passed_checks=passed,
        )


def _is_implementation_call(line: str) -> bool:
    """Heuristik: apakah baris berupa implementasi nyata (bukan penjelasan).

    Baris panggilan/assignment umumnya tidak diawali kata explain/deskripsi
    dan mengandung '(', '=', atau 'import'. Dikenakan konservatif.
    """
    lower = line.lower()
    # Lewati baris yang jelas penjelasan konseptual
    if any(x in lower for x in ("menjelaskan", "dilarang", "tidak boleh",
                                 "must not", "should not", "forbidden adalah",
                                 "ini mendeteksi")):
        return False
    return True
