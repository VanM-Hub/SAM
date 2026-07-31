"""Conversation Tool — bridge conversation <-> tool (Sprint 245).

Program B — Model Runtime Integration.
Read-only bridge; generic, tidak execute tool, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .tool_descriptor import ToolDescriptor
from .tool_preview import ToolPreviewEngine, ToolPreview


@dataclass(frozen=True)
class ConversationToolResult:
    """Hasil tool pada konteks percakapan (immutable)."""
    conversation_id: str
    preview: ToolPreview
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "preview": self.preview.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationTool:
    """Bridge conversation <-> tool. Read-only, tidak mengeksekusi tool."""

    def __init__(self) -> None:
        self._preview = ToolPreviewEngine()

    def call_preview(
        self, conversation_id: str, tool: ToolDescriptor, arguments: Dict[str, object]
    ) -> ConversationToolResult:
        preview = self._preview.preview(tool, arguments)
        return ConversationToolResult(
            conversation_id=conversation_id,
            preview=preview,
            preview_only=True,
            external_calls=0,
        )
