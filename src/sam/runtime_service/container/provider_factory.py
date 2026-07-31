"""ProviderFactory (Sprint 265).

Program D - Runtime Services & Deployment.
Factory untuk membuat provider registration.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ProviderRegistration:
    """Registrasi provider (immutable)."""
    name: str
    kind: str = "llm"
    source: str = "env"
    enabled: bool = True


class ProviderFactory:
    """Factory provider registration (sync, deterministic)."""

    def __init__(self) -> None:
        self._registry: Dict[str, ProviderRegistration] = {}

    def register(self, name: str, kind: str = "llm",
                 enabled: bool = True) -> None:
        if name in self._registry:
            raise ValueError(f"provider already registered: {name}")
        self._registry[name] = ProviderRegistration(
            name=name, kind=kind, enabled=enabled
        )

    def create(self, name: str) -> ProviderRegistration:
        reg = self._registry.get(name)
        if reg is None:
            raise KeyError(f"provider not registered: {name}")
        return reg

    def names(self) -> list:
        return sorted(n for n, r in self._registry.items() if r.enabled)

    def count(self) -> int:
        return len(self._registry)
