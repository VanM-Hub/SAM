"""ArtifactReport — laporan representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactReport:
    total: int = 0
    ready: bool = True
    external_calls: int = 0


class ArtifactReporter:
    """Penyusun laporan artifact. Deterministic & read-only."""

    def report(self, total: int = 0) -> ArtifactReport:
        return ArtifactReport(total=total, ready=True, external_calls=0)
