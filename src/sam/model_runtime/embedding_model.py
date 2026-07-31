"""Embedding Model — representasi model embedding (Sprint 242).

Program B — Model Runtime Integration.
Hanya representasi; tidak menghasilkan embedding asli. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..model_runtime.model_parameters import ModelParameters


@dataclass(frozen=True)
class EmbeddingModel:
    """Model embedding (immutable). Preview-only, no vector produced."""
    embedding_id: str
    name: str
    dimension_hint: Optional[int] = None   # hanya petunjuk representasi
    supports_batch: bool = True
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "embedding_id": self.embedding_id,
            "name": self.name,
            "dimension_hint": self.dimension_hint,
            "supports_batch": self.supports_batch,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
