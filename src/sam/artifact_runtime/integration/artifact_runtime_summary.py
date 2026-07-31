"""ArtifactRuntimeSummary — ringkasan integrasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .artifact_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class ArtifactRuntimeSummary:
    """Ringkasan integrasi Artifact Runtime. Immutable."""
    total_stages: int = len(INTEGRATION_ROUTE)
    container_index: int = INTEGRATION_ROUTE.index("artifact")
    integrated: bool = True
    external_calls: int = 0


class ArtifactRuntimeSummarizer:
    """Penyusun ringkasan integrasi artifact. Deterministic & read-only."""

    def summarize(self) -> ArtifactRuntimeSummary:
        return ArtifactRuntimeSummary()
