"""Conversation Embedding — bridge conversation <-> embedding (Sprint 242).

Program B — Model Runtime Integration.
Read-only bridge; representasi saja, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .embedding_request import EmbeddingRequest
from .embedding_result import EmbeddingResult
from .embedding_preview import EmbeddingPreviewEngine, EmbeddingPreview


@dataclass(frozen=True)
class ConversationEmbeddingResult:
    """Hasil embedding pada konteks percakapan (immutable)."""
    conversation_id: str
    request: EmbeddingRequest
    preview: EmbeddingPreview
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "request": self.request.as_dict(),
            "preview": self.preview.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationEmbedding:
    """Bridge conversation <-> embedding. Read-only, no network."""

    def __init__(self) -> None:
        self._preview = EmbeddingPreviewEngine()

    def embed_preview(
        self, conversation_id: str, texts, input_type: str = "search_document"
    ) -> ConversationEmbeddingResult:
        request = EmbeddingRequest(
            request_id=f"emb-{conversation_id}",
            texts=list(texts),
            input_type=input_type,
            external_calls=0,
        )
        preview = self._preview.preview(request)
        return ConversationEmbeddingResult(
            conversation_id=conversation_id,
            request=request,
            preview=preview,
            preview_only=True,
            external_calls=0,
        )
