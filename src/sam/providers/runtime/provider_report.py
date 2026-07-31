"""Provider Runtime Report — laporan runtime (read-only).

Sprint 154 — Provider Runtime.
Laporan ringkas Provider Runtime. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan runtime (immutable)."""
    runtime_version: str = "1.0.0"
    total_providers: int = 0
    types: Dict[str, int] = field(default_factory=dict)
    ready: bool = False


class ProviderRuntimeReporter:
    """Reporter runtime provider. Read-only."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def report(self) -> RuntimeReport:
        types = {}
        for pid in self._registry.list_ids():
            desc = self._registry.get(pid)
            t = desc.provider_type if desc else "generic"
            types[t] = types.get(t, 0) + 1
        return RuntimeReport(
            runtime_version="1.0.0",
            total_providers=self._registry.count(),
            types=types,
            ready=self._registry.count() > 0,
        )


__all__ = ["ProviderRuntimeReporter", "RuntimeReport"]
