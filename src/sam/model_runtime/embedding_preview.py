"""Embedding Preview — preview deterministik embedding (Sprint 242).

Program B — Model Runtime Integration.
Hanya representasi, tidak menghitung vektor. Preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .embedding_request import EmbeddingRequest
from .embedding_result import EmbeddingResult, EmbeddingVector


@dataclass(frozen=True)
class EmbeddingPreview:
    """Preview embedding (immutable, representasi)."""
    preview_id: str
    request_id: str
    text_count: int = 0
    dimension_hint: int = 768
    would_compute: bool = False  # representasi, bukan inferensi
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "request_id": self.request_id,
            "text_count": self.text_count,
            "dimension_hint": self.dimension_hint,
            "would_compute": self.would_compute,
            "external_calls": self.external_calls,
        }


class EmbeddingPreviewEngine:
    """Preview embedding. Deterministik, no-network, no vector computation."""

    def preview(self, request: EmbeddingRequest, dimension_hint: int = 768) -> EmbeddingPreview:
        return EmbeddingPreview(
            preview_id=f"pv-{request.request_id}",
            request_id=request.request_id,
            text_count=len(request.texts),
            dimension_hint=dimension_hint,
            would_compute=False,
            external_calls=0,
        )
