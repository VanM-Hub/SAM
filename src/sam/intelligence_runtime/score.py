"""Sprint 267 - Certification: score (skor sertifikasi deterministik)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CertificationScore:
    """Skor sertifikasi: berapa dimensi lulus dari total."""

    passed: int = 0
    total: int = 7

    @property
    def ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    @classmethod
    def from_results(cls, results: Dict[str, bool]) -> "CertificationScore":
        passed = sum(1 for v in results.values() if v)
        return cls(passed=passed, total=len(results))

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total": self.total,
            "ratio": self.ratio,
        }
