"""Memory Runtime Report — laporan runtime integrasi (Sprint 179)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry
from .memory_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class MemoryRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_memories: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class MemoryRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def report(self) -> MemoryRuntimeReport:
        return MemoryRuntimeReport(
            total_memories=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
