"""Reasoning Model — representasi model reasoning (Sprint 243).

Program B — Model Runtime Integration.
Hanya struktur reasoning; tidak melakukan reasoning. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReasoningModel:
    """Model reasoning (immutable). No actual reasoning performed."""
    reasoning_id: str
    name: str
    supports_plan: bool = True
    max_steps_hint: int = 8
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "reasoning_id": self.reasoning_id,
            "name": self.name,
            "supports_plan": self.supports_plan,
            "max_steps_hint": self.max_steps_hint,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
