"""CertificationReport (Sprint 270).

Program D - Runtime Services & Deployment.
Laporan sertifikasi runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .certifier import DimensionResult, RuntimeCertifier


@dataclass(frozen=True)
class CertificationReport:
    """Laporan sertifikasi (immutable)."""
    version: str = "27.0.0"
    certified: bool = False
    passed: int = 0
    total: int = 7
    dimensions: List[DimensionResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "certified": self.certified,
            "passed": self.passed,
            "total": self.total,
            "dimensions": [
                {"dimension": d.dimension, "passed": d.passed,
                 "detail": d.detail}
                for d in self.dimensions
            ],
        }


def build_certification_report(certifier: RuntimeCertifier) -> CertificationReport:
    """Bangun laporan dari hasil certifier."""
    return CertificationReport(
        certified=certifier.is_certified(),
        passed=certifier.passed(),
        total=len(certifier.DIMENSIONS),
        dimensions=certifier.results(),
    )
