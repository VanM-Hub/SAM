"""Sprint 278 - Desktop Certification: report (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .certification_dimension import CertificationDimension


@dataclass(frozen=True)
class DesktopCertReport:
    """Laporan sertifikasi desktop read-only."""

    runtime: str = "desktop_runtime"
    version: str = "29.0.0"
    dimensions: Tuple[CertificationDimension, ...] = ()

    @classmethod
    def from_list(cls, dimensions: List[CertificationDimension]) -> "DesktopCertReport":
        return cls(dimensions=tuple(dimensions))

    @property
    def passed(self) -> bool:
        return all(d.passed for d in self.dimensions)

    @property
    def failed_dimensions(self) -> Tuple[str, ...]:
        return tuple(d.name for d in self.dimensions if not d.passed)

    def as_dict(self) -> dict:
        return {
            "runtime": self.runtime,
            "version": self.version,
            "passed": self.passed,
            "dimensions": [d.as_dict() for d in self.dimensions],
            "failed_dimensions": list(self.failed_dimensions),
        }
