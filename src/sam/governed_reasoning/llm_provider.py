"""LLM Provider Integration - WP-01 (MISSION-4.4 / IP-4.4-001).

Menghubungkan LLM sebagai Provider operasional melalui arsitektur Provider.
Minimal satu LLM Provider terhubung, terdaftar sebagai Citizen, health status
tersedia, mengikuti Provider Contract, tanpa dependency langsung ke
implementation provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass(frozen=True)
class ProviderCapabilityDescriptor:
    """Deskripsi capability sebuah LLM provider."""

    provider_id: str
    capabilities: Tuple[str, ...] = field(default_factory=tuple)
    max_tokens: int = 0
    models: Tuple[str, ...] = field(default_factory=tuple)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "capabilities": list(self.capabilities),
            "max_tokens": self.max_tokens,
            "models": list(self.models),
        }


@dataclass(frozen=True)
class ProviderMetadata:
    """Metadata provider LLM."""

    provider_id: str
    name: str = ""
    vendor: str = ""
    model: str = ""
    version: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "vendor": self.vendor,
            "model": self.model,
            "version": self.version,
        }


@dataclass(frozen=True)
class ProviderHealthStatus:
    """Status kesehatan provider."""

    provider_id: str
    healthy: bool = False
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "healthy": self.healthy,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class LLMProviderAdapter:
    """Adapter provider LLM (abstraksi; tanpa vendor-specific dependency)."""

    metadata: ProviderMetadata
    capability: ProviderCapabilityDescriptor
    invoke: Callable[..., Any]

    def as_dict(self) -> dict:
        return {
            "metadata": self.metadata.as_dict(),
            "capability": self.capability.as_dict(),
        }


class LLMProviderRegistry:
    """Registry LLM provider (discovery & registration read-only)."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProviderAdapter] = {}

    def register(self, adapter: LLMProviderAdapter) -> None:
        self._providers[adapter.metadata.provider_id] = adapter

    def get(self, provider_id: str) -> Optional[LLMProviderAdapter]:
        return self._providers.get(provider_id)

    def discover(self, capability: str = "") -> Tuple[LLMProviderAdapter, ...]:
        if not capability:
            return tuple(self._providers.values())
        return tuple(
            p
            for p in self._providers.values()
            if p.capability.supports(capability)
        )

    def list_providers(self) -> Tuple[str, ...]:
        return tuple(self._providers.keys())

    def health(self, provider_id: str) -> ProviderHealthStatus:
        adapter = self._providers.get(provider_id)
        if adapter is None:
            return ProviderHealthStatus(provider_id, False, "unknown provider")
        try:
            result = adapter.invoke(_health_probe=True)
            if result is None:
                # provider tanpa probe -> healthy pasif (registered)
                return ProviderHealthStatus(provider_id, True, "registered")
            return ProviderHealthStatus(
                provider_id, bool(result.get("healthy", False)), str(result.get("detail", ""))
            )
        except Exception as exc:
            return ProviderHealthStatus(provider_id, False, str(exc))

    def count(self) -> int:
        return len(self._providers)
