"""Provider Runtime — engine runtime utama Provider Runtime.

Sprint 144 — Provider Foundation (OP-1408).
Runtime integration: menggabungkan registry menjadi satu runtime terpadu.
Hanya mengatur lifecycle; bukan provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class ProviderRuntimeCheck:
    """Hasil cek satu tahap runtime."""
    stage: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class ProviderRuntimeReadiness:
    """Kesiapan Provider Runtime."""
    ready: bool = False
    checks: List[ProviderRuntimeCheck] = field(default_factory=list)


class ProviderRuntime:
    """Runtime utama Provider Runtime — mengorkestrasi registry & lifecycle."""

    RUNTIME_VERSION = "1.0.0"

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._ready = False

    def readiness(self) -> ProviderRuntimeReadiness:
        checks = []
        total = self._registry.count()
        checks.append(
            ProviderRuntimeCheck("registry", total > 0, f"{total} providers")
        )
        with_cap = sum(
            1 for pid in self._registry.list_ids()
            if self._registry.get_capabilities(pid)
        )
        checks.append(
            ProviderRuntimeCheck("capability", with_cap > 0, f"{with_cap} with capability")
        )
        all_ok = all(c.ok for c in checks) and total > 0
        self._ready = all_ok
        return ProviderRuntimeReadiness(all_ok, checks)

    def status(self) -> bool:
        return self._ready or self.readiness().ready

    def registry(self) -> ProviderRegistry:
        return self._registry
