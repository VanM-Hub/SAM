"""Execution Verification - IP-4.1-002 WP-13.

Governed Execution.
Verifikasi hasil eksekusi (apakah sesuai yang diharapkan), berbasis evidence.

Scope (Foundation immutable):
- Eksekusi terverifikasi setelah berjalan.
- Hasil verifikasi berbasis evidence (status, external_calls, dsb).
- Deterministik (Article VII).
- Tidak menambah authority; hanya penilaian hasil read-only.

Tidak ada network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple


@dataclass(frozen=True)
class VerificationCriterion:
    """Satu kriteria verifikasi (immutable)."""

    name: str
    met: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "met": self.met, "detail": self.detail}


@dataclass(frozen=True)
class ExecutionVerification:
    """Hasil verifikasi execution (immutable)."""

    verification_id: str
    execution_id: str
    passed: bool
    criteria: Tuple[VerificationCriterion, ...] = field(default_factory=tuple)
    verified_at: str = ""

    def as_dict(self) -> dict:
        return {
            "verification_id": self.verification_id,
            "execution_id": self.execution_id,
            "passed": self.passed,
            "criteria": [c.as_dict() for c in self.criteria],
            "verified_at": self.verified_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionVerifier:
    """Memverifikasi hasil sebuah eksekusi (read-only)."""

    def verify(self, request, response, expected_status: str = "") -> ExecutionVerification:
        """Verifikasi hasil eksekusi.

        Kriteria:
        1. Status response sesuai harapan (default: completed utk execute,
           preview utk mode non-execute).
        2. Mode execute memang punya external_calls (bila execute).
        3. Tidak ada error fatal.
        """
        criteria: list = []
        response_status = getattr(response, "status", "unknown")
        mode = getattr(request, "mode", "preview")
        if not expected_status:
            expected_status = "completed" if mode == "execute" else mode or "preview"

        # Kriteria 1: status sesuai harapan
        status_ok = response_status == expected_status
        criteria.append(VerificationCriterion(
            "status", status_ok,
            "status '{}' == '{}'".format(response_status, expected_status)))

        # Kriteria 2: external_calls konsisten (execute -> boleh >0; preview -> 0)
        calls = getattr(response, "external_calls", 0)
        mode_ok = (calls > 0) if mode == "execute" else (calls == 0)
        criteria.append(VerificationCriterion(
            "external_calls", mode_ok,
            "external_calls={} (mode={})".format(calls, mode)))

        # Kriteria 3: tidak ada error fatal
        error = getattr(response, "error", None)
        error_ok = error is None or error == "" or response_status != "failed"
        criteria.append(VerificationCriterion(
            "no_fatal_error", error_ok,
            "error={}".format(error) if error else "no error"))

        passed = all(c.met for c in criteria)
        return ExecutionVerification(
            verification_id="ver-{}".format(getattr(request, "execution_id", "?")),
            execution_id=getattr(request, "execution_id", ""),
            passed=passed,
            criteria=tuple(criteria),
            verified_at=_now(),
        )
