"""Connector Runtime — engine runtime utama connector.

Sprint 121 — Connector Runtime.
Orkestrasi pipeline connector dari foundation sampai preview. Preview-only, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class RuntimeCheck:
    """Hasil cek satu tahap runtime."""
    stage: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class RuntimeReadiness:
    """Kesiapan runtime connector."""
    ready: bool = False
    checks: List[RuntimeCheck] = field(default_factory=list)


class ConnectorRuntime:
    """Runtime utama connector — mengorkestrasi tahapan.

    Pipeline: registry -> capability -> binding (mirror phase).
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def readiness(self) -> RuntimeReadiness:
        checks = []
        checks.append(RuntimeCheck("registry", self._registry.count() > 0,
                                   f"{self._registry.count()} connectors"))
        with_cap = self._count_with_capabilities()
        checks.append(RuntimeCheck("capability", with_cap > 0,
                                   f"{with_cap} with capabilities"))
        # binding opsional di preview — selalu siap jika ada capability
        checks.append(RuntimeCheck("binding", with_cap > 0,
                                   "binding ready"))
        all_ok = all(c.ok for c in checks) and self._registry.count() > 0
        return RuntimeReadiness(all_ok, checks)

    def _count_with_capabilities(self) -> int:
        return sum(1 for cid in self._registry.list_ids()
                   if self._registry.get_capabilities(cid))
