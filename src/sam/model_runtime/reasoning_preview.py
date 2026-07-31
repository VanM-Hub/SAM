"""Reasoning Preview — preview deterministik reasoning (Sprint 243).

Program B — Model Runtime Integration.
Menyiapkan struktur rencana; TIDAK melakukan reasoning. external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .reasoning_plan import ReasoningPlan
from .reasoning_step import ReasoningStep


@dataclass(frozen=True)
class ReasoningPreview:
    """Preview reasoning (immutable, representasi)."""
    preview_id: str
    goal: str = ""
    planned_steps: int = 0
    note: str = "structure only - no reasoning performed"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "goal": self.goal,
            "planned_steps": self.planned_steps,
            "note": self.note,
            "external_calls": self.external_calls,
        }


class ReasoningPreviewEngine:
    """Preview reasoning. Menyusun struktur langkah, tanpa inferensi."""

    def preview(self, goal: str, planned_steps: int = 3) -> ReasoningPreview:
        return ReasoningPreview(
            preview_id="pv-reason",
            goal=goal,
            planned_steps=max(0, planned_steps),
            note="structure only - no reasoning performed",
            external_calls=0,
        )

    def build_plan(self, goal: str, steps: List[str] | None = None) -> ReasoningPlan:
        """Susun rencana dengan langkah representasi (tanpa reasoning)."""
        entries = steps or [f"step {i + 1}" for i in range(3)]
        plan_steps = [
            ReasoningStep(step_index=i, kind="thought", content=c)
            for i, c in enumerate(entries)
        ]
        return ReasoningPlan(
            plan_id="plan-reason",
            goal=goal,
            steps=plan_steps,
            preview_only=True,
            external_calls=0,
        )
