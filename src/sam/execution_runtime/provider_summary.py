"""Provider Summary (Sprint 253).

Program C - Real Execution Runtime.
Rangkuman immutable hasil dispatch per provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .provider_history import ProviderHistoryEntry


@dataclass(frozen=True)
class ProviderSummaryData:
    """Ringkasan satu provider (immutable)."""
    provider_id: str
    dispatches: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "dispatches": self.dispatches,
            "external_calls": self.external_calls,
        }


class ProviderSummary:
    """Rangkuman per provider dari history. Read-only."""

    def summarize(self, entries: List[ProviderHistoryEntry]) -> List[ProviderSummaryData]:
        acc: Dict[str, ProviderSummaryData] = {}
        for e in entries:
            cur = acc.get(e.provider_id, ProviderSummaryData(provider_id=e.provider_id))
            acc[e.provider_id] = ProviderSummaryData(
                provider_id=e.provider_id,
                dispatches=cur.dispatches + 1,
                external_calls=cur.external_calls + e.external_calls,
            )
        return [acc[k] for k in sorted(acc)]
