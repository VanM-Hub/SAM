"""ArtifactRuntimeReport — laporan integrasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .artifact_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class ArtifactRuntimeReport:
    """Laporan integrasi Artifact Runtime. Immutable."""
    total_artifact: int = 0
    route: Tuple[str, ...] = INTEGRATION_ROUTE
    preview_only: bool = True
    no_storage: bool = True
    no_publish: bool = True
    ready: bool = True
    external_calls: int = 0


class ArtifactRuntimeReporter:
    """Penyusun laporan integrasi artifact. Deterministic & read-only."""

    def __init__(self, registry) -> None:
        self._registry = registry

    def report(self) -> ArtifactRuntimeReport:
        return ArtifactRuntimeReport(
            total_artifact=self._registry.count(),
            route=INTEGRATION_ROUTE,
            preview_only=True, no_storage=True, no_publish=True,
            ready=True, external_calls=0,
        )
