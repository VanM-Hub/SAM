"""Provider Factory — pabrik provider plug-in (Sprint 228).

Program A — External Connector Integration.
Factory membuat instance provider berbasis provider_id. Semua provider
bersifat plug-in: cukup daftarkan ke factory, lalu dibuat via interface yang sama.
Tidak ada provider-specific logic di sini.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ProviderFactoryEntry:
    """Deskripsi entry factory untuk satu tipe provider."""
    provider_id: str
    adapter_type: str
    builder_name: str
    version: str = "1.0.0"


class ProviderFactory:
    """Registry pembuat provider (plug-in). Sinkronus, deterministik, preview-only."""

    def __init__(self) -> None:
        self._builders: Dict[str, Callable[[], Any]] = {}
        self._entries: Dict[str, ProviderFactoryEntry] = {}

    def register(
        self,
        provider_id: str,
        builder: Callable[[], Any],
        adapter_type: str = "adapter",
        builder_name: str = "default",
        version: str = "1.0.0",
    ) -> bool:
        if provider_id in self._builders:
            return False
        self._builders[provider_id] = builder
        self._entries[provider_id] = ProviderFactoryEntry(
            provider_id=provider_id,
            adapter_type=adapter_type,
            builder_name=builder_name,
            version=version,
        )
        return True

    def create(self, provider_id: str) -> Any:
        if provider_id not in self._builders:
            raise KeyError(f"no builder registered for provider '{provider_id}'")
        return self._builders[provider_id]()

    def has(self, provider_id: str) -> bool:
        return provider_id in self._builders

    def entry(self, provider_id: str) -> Optional[ProviderFactoryEntry]:
        return self._entries.get(provider_id)

    def list_ids(self) -> list:
        return sorted(self._builders.keys())

    def count(self) -> int:
        return len(self._builders)
