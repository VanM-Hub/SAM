"""Rollback Summary (Sprint 255).

Program C - Real Execution Runtime.
Rangkuman immutable agregat rollback.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .rollback_report import RollbackReport


@dataclass(frozen=True)
class RollbackSummary:
    """Ringkasan rollback (immutable)."""
    total: int = 0
    ok: int = 0
    failed: int = 0
    external_calls: int = 0

    def add(self, report: RollbackReport) -> "RollbackSummary":
        return RollbackSummary(
            total=self.total + 1,
            ok=self.ok + (1 if report.status == "ok" else 0),
            failed=self.failed + (1 if report.status == "failed" else 0),
            external_calls=self.external_calls + report.external_calls,
        )

    def to_dict(self) -> dict:
        return {"total": self.total, "ok": self.ok,
                "failed": self.failed, "external_calls": self.external_calls}
