"""Embedding Request — request embedding (Sprint 242).

Program B — Model Runtime Integration.
Hanya representasi; tidak menghasilkan embedding asli. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model_runtime.model_parameters import ModelParameters


@dataclass(frozen=True)
class EmbeddingRequest:
    """Request embedding (immutable). Representasi teks/label saja."""
    request_id: str
    texts: List[str] = field(default_factory=list)
    input_type: str = "search_document"  # search_document | search_query | clustering
    parameters: ModelParameters = field(default_factory=ModelParameters)
    mode: str = "preview"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "texts": list(self.texts),
            "input_type": self.input_type,
            "parameters": self.parameters.as_dict(),
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
