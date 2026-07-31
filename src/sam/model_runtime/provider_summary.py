"""Provider Summary — ringkasan mapping provider (Sprint 247).

Program B — Model Runtime Integration.
Ringkasan read-only; belum network. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .provider_matrix import ProviderMatrix


@dataclass(frozen=True)
class ProviderSummary:
    """Ringkasan provider (immutable)."""
    summary_id: str
    count: int = 0
    by_capability: Dict[str, int] = field(default_factory=dict)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "summary_id": self.summary_id,
            "count": self.count,
            "by_capability": dict(self.by_capability),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ProviderSummarizer:
    """Merangkum matriks provider. Read-only, no-network."""

    def summarize(self, matrix: ProviderMatrix) -> ProviderSummary:
        counts: Dict[str, int] = {}
        for profile in matrix.profiles:
            for cap in profile.capabilities:
                counts[cap] = counts.get(cap, 0) + 1
        return ProviderSummary(
            summary_id="provider-summary",
            count=len(matrix.profiles),
            by_capability=counts,
            preview_only=True,
            external_calls=0,
        )
