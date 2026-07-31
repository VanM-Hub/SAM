"""Execution Summary (Sprint 254).

Program C - Real Execution Runtime.
Rangkuman immutable agregat dari banyak eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_report import ExecutionReport


@dataclass(frozen=True)
class ExecutionSummary:
    """Ringkasan eksekusi (immutable)."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    external_calls: int = 0

    def add(self, report: ExecutionReport) -> "ExecutionSummary":
        return ExecutionSummary(
            total=self.total + 1,
            completed=self.completed + (1 if report.status == "completed" else 0),
            failed=self.failed + (1 if report.status == "failed" else 0),
            external_calls=self.external_calls + report.external_calls,
        )

    def to_dict(self) -> dict:
        return {"total": self.total, "completed": self.completed,
                "failed": self.failed, "external_calls": self.external_calls}
