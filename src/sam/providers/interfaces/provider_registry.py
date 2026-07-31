"""Provider Registry — registri interface provider (Sprint 228).

Program A — External Connector Integration.
Registry generik untuk metadata/entri semua provider plug-in.
Berbeda implementasi dari providers/registry (Phase XIV) namun melengkapi
sebagai layer interface yang sama untuk Program A.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class ProviderRegistryEntry:
    """Entri registri sebuah provider (immutable)."""
    provider_id: str
    name: str
    kind: str = "llm"  # llm | connector | local | execution
    enabled: bool = True
    preview_only: bool = True
    external_calls: int = 0
    tags: Tuple[str, ...] = field(default_factory=tuple)


class ProviderRegistry:
    """Registry interface provider — daftar provider plug-in (preview-first)."""

    def __init__(self) -> None:
        self._entries: Dict[str, ProviderRegistryEntry] = {}

    def register(self, entry: ProviderRegistryEntry) -> bool:
        if entry.provider_id in self._entries:
            return False
        self._entries[entry.provider_id] = entry
        return True

    def get(self, provider_id: str) -> Optional[ProviderRegistryEntry]:
        return self._entries.get(provider_id)

    def list_ids(self) -> list:
        return sorted(self._entries.keys())

    def count(self) -> int:
        return len(self._entries)

    def enabled_ids(self) -> list:
        return sorted(
            pid for pid, e in self._entries.items() if e.enabled
        )

    def by_kind(self, kind: str) -> list:
        return sorted(
            pid for pid, e in self._entries.items() if e.kind == kind
        )

    def entries(self) -> Tuple[ProviderRegistryEntry, ...]:
        return tuple(
            self._entries[pid] for pid in sorted(self._entries.keys())
        )
