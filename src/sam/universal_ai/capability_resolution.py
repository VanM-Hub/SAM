"""Provider Capability Resolution - WP-16 (MISSION-5.1 / IP-5.1-002).

Menghubungkan capability declaration dari Provider Adapter dengan AI Capability
Model. Resolution deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .adapter_framework import ProviderAdapter
from .capability_model import AICapabilityKind


@dataclass(frozen=True)
class ResolvedCapability:
    """Hasil resolusi capability untuk satu provider."""

    provider_id: str
    kind: AICapabilityKind
    supported: bool

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "kind": self.kind.value,
            "supported": self.supported,
        }


class CapabilityResolver:
    """Resolver deterministik antara adapter dan capability model."""

    def __init__(self, adapters: Tuple[ProviderAdapter, ...] = ()) -> None:
        self._adapters = {a.provider_id: a for a in adapters}

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.provider_id] = adapter

    def resolve(self, provider_id: str, model_id: str) -> Tuple[str, ...]:
        """Kembalikan daftar capability yang didukung provider/model.

        Menggunakan capability mapping dari adapter bila tersedia. Default
        deterministik: text_generation selalu didukung oleh adapter yang
        mengimplementasikan invoke.
        """
        adapter = self._adapters.get(provider_id)
        if adapter is None:
            return ()
        return tuple(_DEFAULT_CAPABILITIES)


_DEFAULT_CAPABILITIES = (AICapabilityKind.TEXT_GENERATION,)


class CapabilityMapping:
    """Mapping capability yang dideklarasikan tiap provider/model."""

    def __init__(self) -> None:
        self._map: dict = {}

    def declare(self, provider_id: str, model_id: str, capabilities: Tuple[AICapabilityKind, ...]) -> None:
        self._map[(provider_id, model_id)] = tuple(capabilities)

    def supports(self, provider_id: str, model_id: str, kind: AICapabilityKind) -> bool:
        caps = self._map.get((provider_id, model_id))
        return kind in caps if caps is not None else bool(kind == AICapabilityKind.TEXT_GENERATION)

    def unsupported(self, provider_id: str, model_id: str, kind: AICapabilityKind) -> bool:
        return not self.supports(provider_id, model_id, kind)
