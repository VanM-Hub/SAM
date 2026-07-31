"""Runtime Coordinator — engine koordinator connector runtime.

Sprint 121 — Connector Runtime.
Koordinasi seluruh engine connector menjadi satu runtime terpadu.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry
from .runtime import ConnectorRuntime, RuntimeReadiness
from .runtime_pipeline import RuntimePipeline, RuntimePipelineBuilder


@dataclass(frozen=True)
class CoordinationResult:
    """Hasil koordinasi runtime."""
    ready: bool = False
    message: str = ""


class RuntimeCoordinator:
    """Koordinator connector runtime."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._runtime = ConnectorRuntime(registry)
        self._pipeline = RuntimePipelineBuilder().build()

    def readiness(self) -> RuntimeReadiness:
        return self._runtime.readiness()

    def pipeline(self) -> RuntimePipeline:
        return self._pipeline

    def health(self) -> CoordinationResult:
        r = self._runtime.readiness()
        return CoordinationResult(r.ready,
                                  "ready" if r.ready else "not ready")
