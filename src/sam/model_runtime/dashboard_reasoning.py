"""Dashboard Reasoning — bridge dashboard <-> reasoning (Sprint 243).

Program B — Model Runtime Integration.
Read-only bridge; struktur reasoning saja, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .reasoning_plan import ReasoningPlan


@dataclass(frozen=True)
class DashboardReasoningRow:
    """Satu baris reasoning pada dashboard (immutable)."""
    row_id: str
    plan_id: str
    goal: str = ""
    steps: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": self.steps,
            "external_calls": self.external_calls,
        }


class DashboardReasoning:
    """Bridge dashboard <-> reasoning. Read-only, no network."""

    def __init__(self) -> None:
        self._rows: List[DashboardReasoningRow] = []

    def add(self, plan: ReasoningPlan) -> None:
        self._rows.append(DashboardReasoningRow(
            row_id=f"dreason-{len(self._rows) + 1}",
            plan_id=plan.plan_id,
            goal=plan.goal,
            steps=plan.step_count(),
            external_calls=plan.external_calls,
        ))

    def rows(self) -> List[DashboardReasoningRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        return {
            "plans": len(self._rows),
            "steps": sum(r.steps for r in self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
