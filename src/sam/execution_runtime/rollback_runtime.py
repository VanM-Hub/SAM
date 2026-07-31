"""Rollback Runtime (Sprint 255).

Program C - Real Execution Runtime.
Runtime rollback. Rollback HANYA memulihkan metadata internal, TIDAK pernah
membatalkan efek di external world (tanpa network call, external_calls=0).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .rollback_request import RollbackRequest
from .rollback_plan import RollbackPlan
from .rollback_report import RollbackReport
from .rollback_summary import RollbackSummary


@dataclass(frozen=True)
class RollbackOutcome:
    """Outcome rollback (immutable)."""
    runtime_id: str
    plan: RollbackPlan
    report: RollbackReport
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"runtime_id": self.runtime_id, "plan": self.plan.as_dict(),
                "report": self.report.as_dict(), "external_calls": self.external_calls}


class RollbackRuntime:
    """Rollback runtime. Metadata-only, no external side effect."""

    def __init__(self) -> None:
        self._snapshot: Dict[str, Any] = {}
        self._summary = RollbackSummary()

    def capture_metadata(self, key: str, value: Any) -> None:
        """Simpan snapshot metadata untuk pemulihan (internal state)."""
        self._snapshot[key] = value

    def run(self, request: RollbackRequest) -> RollbackOutcome:
        plan = RollbackPlan(plan_id=f"plan-{request.rollback_id}", request=request,
                            metadata_keys=tuple(self._snapshot.keys()), scope="metadata")
        restored = []
        for key in plan.metadata_keys:
            if key in self._snapshot:
                restored.append(key)
        report = RollbackReport(
            report_id=f"rb-{request.rollback_id}",
            rollback_id=request.rollback_id,
            execution_id=request.execution_id,
            status="ok",
            restored_metadata=tuple(restored),
            external_calls=0,
        )
        self._summary = self._summary.add(report)
        return RollbackOutcome(runtime_id=f"rb-rt-{request.rollback_id}", plan=plan,
                               report=report, external_calls=0)

    def summary(self) -> dict:
        return self._summary.to_dict()
