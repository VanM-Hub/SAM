"""Cognitive Runtime Report — laporan runtime integrasi (Sprint 195)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class CognitiveRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_cognitive: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class CognitiveRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def report(self) -> CognitiveRuntimeReport:
        return CognitiveRuntimeReport(
            total_cognitive=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
