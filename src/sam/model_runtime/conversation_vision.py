"""Conversation Vision — bridge conversation <-> vision (Sprint 244).

Program B — Model Runtime Integration.
Read-only bridge; representasi image input, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .vision_input import VisionInput
from .vision_request import VisionRequest
from .vision_preview import VisionPreviewEngine, VisionPreview


@dataclass(frozen=True)
class ConversationVisionResult:
    """Hasil vision pada konteks percakapan (immutable)."""
    conversation_id: str
    preview: VisionPreview
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "preview": self.preview.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationVision:
    """Bridge conversation <-> vision. Read-only, no inference."""

    def __init__(self) -> None:
        self._preview = VisionPreviewEngine()

    def preview_images(self, conversation_id: str, images: List[VisionInput]) -> ConversationVisionResult:
        request = VisionRequest(
            request_id=f"vis-{conversation_id}",
            images=list(images),
            external_calls=0,
        )
        preview = self._preview.preview(request)
        return ConversationVisionResult(
            conversation_id=conversation_id,
            preview=preview,
            preview_only=True,
            external_calls=0,
        )
