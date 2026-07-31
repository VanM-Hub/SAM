"""Provider History (Sprint 253).

Program C - Real Execution Runtime.
Riwayat immutable dispatch per provider. Read-only, no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .provider_dispatcher import DispatchTarget


@dataclass(frozen=True)
class ProviderHistoryEntry:
    """Satu entri riwayat provider (immutable)."""
    entry_id: str
    provider_id: str
    operation: str
    mode: str = "preview"
    status: str = "dispatched"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "mode": self.mode,
            "status": self.status,
            "external_calls": self.external_calls,
        }


class ProviderHistory:
    """Riwayat dispatch. Append-only, read-only view."""

    def __init__(self) -> None:
        self._entries: List[ProviderHistoryEntry] = []

    def record(self, target: DispatchTarget) -> ProviderHistoryEntry:
        entry = ProviderHistoryEntry(
            entry_id=f"ph-{len(self._entries) + 1}",
            provider_id=target.provider_id,
            operation=target.operation,
            mode=target.mode,
            external_calls=target.external_calls,
        )
        self._entries.append(entry)
        return entry

    def all(self) -> List[ProviderHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def count_by_provider(self, provider_id: str) -> int:
        return sum(1 for e in self._entries if e.provider_id == provider_id)
