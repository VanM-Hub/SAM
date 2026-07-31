"""Reasoning Step — langkah reasoning (Sprint 243).

Program B — Model Runtime Integration.
Representasi struktur langkah reasoning. Immutable, no reasoning.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ReasoningStep:
    """Satu langkah reasoning (immutable, representasi)."""
    step_index: int
    kind: str = "thought"  # thought | observation | decision
    content: str = ""
    note: str = "structure only - no reasoning performed"

    def as_dict(self) -> dict:
        return {
            "step_index": self.step_index,
            "kind": self.kind,
            "content": self.content,
            "note": self.note,
        }
