"""Dashboard Embedding — bridge dashboard <-> embedding (Sprint 242).

Program B — Model Runtime Integration.
Read-only bridge; representasi saja, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .embedding_result import EmbeddingResult


@dataclass(frozen=True)
class DashboardEmbeddingRow:
    """Satu baris embedding pada dashboard (immutable)."""
    row_id: str
    request_id: str
    text_count: int = 0
    filled: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "request_id": self.request_id,
            "text_count": self.text_count,
            "filled": self.filled,
            "external_calls": self.external_calls,
        }


class DashboardEmbedding:
    """Bridge dashboard <-> embedding. Read-only, no network."""

    def __init__(self) -> None:
        self._rows: List[DashboardEmbeddingRow] = []

    def add(self, result: EmbeddingResult) -> None:
        row = DashboardEmbeddingRow(
            row_id=f"demb-{len(self._rows) + 1}",
            request_id=result.request_id,
            text_count=len(result.vectors),
            filled=result.summary.get("filled", False),
            external_calls=result.external_calls,
        )
        self._rows.append(row)

    def rows(self) -> List[DashboardEmbeddingRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        return {
            "embeddings": len(self._rows),
            "external_calls": sum(r.external_calls for r in self._rows),
        }
