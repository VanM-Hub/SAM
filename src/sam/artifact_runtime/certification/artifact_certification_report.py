"""ArtifactCertificationReport — laporan sertifikasi (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactCertificationReport:
    """Laporan hasil sertifikasi. Immutable."""
    certified: bool = True
    score: float = 100.0
    external_calls: int = 0


class ArtifactCertificationReporter:
    """Penyusun laporan sertifikasi. Deterministic & read-only."""

    def report(self, certified: bool = True, score: float = 100.0):
        return ArtifactCertificationReport(certified=certified, score=score,
                                           external_calls=0)
