"""Knowledge Runtime Report — laporan runtime integrasi (Sprint 187)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry
from .knowledge_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class KnowledgeRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_knowledge: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class KnowledgeRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def report(self) -> KnowledgeRuntimeReport:
        return KnowledgeRuntimeReport(
            total_knowledge=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
