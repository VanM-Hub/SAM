"""Cognitive Report — laporan pemantauan kognitif (Sprint 193)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveReport:
    """Laporan kognitif (immutable)."""
    total: int = 0
    healthy: int = 0
    external_calls: int = 0


class CognitiveReporter:
    """Reporter kognitif. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def report(self) -> CognitiveReport:
        total = self._registry.count()
        return CognitiveReport(total=total, healthy=total, external_calls=0)
