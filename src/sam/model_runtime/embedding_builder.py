"""Embedding Builder — builder deterministik embedding (Sprint 242).

Program B — Model Runtime Integration.
Deterministik, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .embedding_model import EmbeddingModel
from .embedding_request import EmbeddingRequest
from .embedding_result import EmbeddingResult, EmbeddingVector


@dataclass(frozen=True)
class EmbeddingBuilder:
    """Builder deterministik untuk representasi embedding."""

    def build_model(
        self,
        embedding_id: str,
        name: str,
        dimension_hint: Optional[int] = 768,
        supports_batch: bool = True,
    ) -> EmbeddingModel:
        return EmbeddingModel(
            embedding_id=embedding_id,
            name=name,
            dimension_hint=dimension_hint,
            supports_batch=supports_batch,
            preview_only=True,
            external_calls=0,
        )

    def build_request(
        self,
        request_id: str,
        texts: List[str] | None = None,
        input_type: str = "search_document",
    ) -> EmbeddingRequest:
        return EmbeddingRequest(
            request_id=request_id,
            texts=list(texts or []),
            input_type=input_type,
            mode="preview",
            external_calls=0,
        )

    def placeholder_result(
        self, request: EmbeddingRequest, dimension_hint: int = 768
    ) -> EmbeddingResult:
        """Hasil representasi placeholder — TIDAK menghitung vektor asli."""
        vectors = [
            EmbeddingVector(index=i, dimension=dimension_hint, filled=False)
            for i in range(len(request.texts))
        ]
        return EmbeddingResult(
            request_id=request.request_id,
            vectors=vectors,
            summary={
                "texts": len(request.texts),
                "filled": False,
                "note": "representation only - no real embedding",
            },
            external_calls=0,
        )
