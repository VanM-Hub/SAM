"""Dashboard Mapping — bridge dashboard <-> provider mapping (Sprint 247).

Program B — Model Runtime Integration.
Read-only bridge; mapping provider, belum network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .provider_matrix import ProviderMatrix
from .provider_summary import ProviderSummarizer, ProviderSummary


@dataclass(frozen=True)
class DashboardMappingRow:
    """Satu baris mapping pada dashboard (immutable)."""
    row_id: str
    provider: str
    capabilities: List[str] = field(default_factory=list)
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "provider": self.provider,
            "capabilities": list(self.capabilities),
            "external_calls": self.external_calls,
        }


class DashboardMapping:
    """Bridge dashboard <-> provider mapping. Read-only, no-network."""

    def __init__(self, summarizer: ProviderSummarizer | None = None) -> None:
        self._summarizer = summarizer or ProviderSummarizer()

    def rows(self, matrix: ProviderMatrix) -> List[DashboardMappingRow]:
        out = []
        for profile in matrix.profiles:
            out.append(DashboardMappingRow(
                row_id=f"dmapp-{profile.provider}",
                provider=profile.provider,
                capabilities=list(profile.capabilities),
                external_calls=profile.external_calls,
            ))
        return out

    def summary(self, matrix: ProviderMatrix) -> ProviderSummary:
        return self._summarizer.summarize(matrix)
