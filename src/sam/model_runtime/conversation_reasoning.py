"""Conversation Reasoning — bridge conversation <-> reasoning (Sprint 243).

Program B — Model Runtime Integration.
Read-only bridge; struktur reasoning saja, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .reasoning_preview import ReasoningPreviewEngine
from .reasoning_plan import ReasoningPlan
from .reasoning_preview import ReasoningPreview


@dataclass(frozen=True)
class ConversationReasoningResult:
    """Hasil reasoning pada konteks percakapan (immutable)."""
    conversation_id: str
    plan: ReasoningPlan
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "plan": self.plan.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationReasoning:
    """Bridge conversation <-> reasoning. Read-only, no reasoning."""

    def __init__(self) -> None:
        self._preview = ReasoningPreviewEngine()

    def plan(self, conversation_id: str, goal: str) -> ConversationReasoningResult:
        plan = self._preview.build_plan(goal)
        return ConversationReasoningResult(
            conversation_id=conversation_id,
            plan=plan,
            preview_only=True,
            external_calls=0,
        )
