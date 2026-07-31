"""Reasoning Summary — ringkasan reasoning (Sprint 243).

Program B — Model Runtime Integration.
Representasi ringkasan. Immutable, no reasoning.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .reasoning_step import ReasoningStep


@dataclass(frozen=True)
class ReasoningSummary:
    """Ringkasan reasoning (immutable, representasi)."""
    summary_id: str
    goal: str = ""
    steps: List[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "summary_id": self.summary_id,
            "goal": self.goal,
            "steps": [s.as_dict() for s in self.steps],
            "conclusion": self.conclusion,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
