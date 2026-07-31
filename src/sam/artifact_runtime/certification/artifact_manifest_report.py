"""ArtifactManifestReport — laporan manifest artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactManifestReport:
    """Laporan manifest artifact untuk sertifikasi. Immutable."""
    subsystems: Tuple[str, ...] = ()
    integrated: int = 0


class ArtifactManifestReporter:
    """Penyusun laporan manifest. Deterministic & read-only."""

    def report(self, subsystems: Tuple[str, ...] = ()) -> ArtifactManifestReport:
        return ArtifactManifestReport(subsystems=tuple(subsystems),
                                      integrated=len(subsystems))
