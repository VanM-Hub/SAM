"""Reasoning Plan — rencana reasoning (Sprint 243).

Program B — Model Runtime Integration.
Hanya struktur rencana; tidak melakukan reasoning. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .reasoning_step import ReasoningStep


@dataclass(frozen=True)
class ReasoningPlan:
    """Rencana reasoning (immutable, representasi)."""
    plan_id: str
    goal: str = ""
    steps: List[ReasoningStep] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [s.as_dict() for s in self.steps],
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }

    def step_count(self) -> int:
        return len(self.steps)
