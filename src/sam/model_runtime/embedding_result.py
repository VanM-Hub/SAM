"""Embedding Result — hasil embedding (Sprint 242).

Program B — Model Runtime Integration.
Hanya representasi — tidak berisi vektor asli dari model. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EmbeddingVector:
    """Representasi vektor (placeholder — bukan vektor asli model)."""
    index: int
    dimension: int = 0
    filled: bool = False  # False = tidak dihitung, hanya representasi

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "dimension": self.dimension,
            "filled": self.filled,
        }


@dataclass(frozen=True)
class EmbeddingResult:
    """Hasil embedding (immutable). Tidak berisi vektor asli."""
    request_id: str
    vectors: List[EmbeddingVector] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "vectors": [v.as_dict() for v in self.vectors],
            "summary": dict(self.summary),
            "external_calls": self.external_calls,
        }
