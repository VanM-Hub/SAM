"""Sprint 267 - Certification: validator (validator 7 dimensi)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


DIMENSIONS = (
    "Structure",
    "Integrity",
    "Consistency",
    "Completeness",
    "Determinism",
    "Immutability",
    "RuntimeCoverage",
)


@dataclass(frozen=True)
class CertificationValidator:
    """Validator 7 dimensi; menerima hasil untuk dinilai secara deterministik."""

    def validate(self, results: Dict[str, bool]) -> Tuple[bool, Tuple[str, ...]]:
        missing = [d for d in DIMENSIONS if d not in results]
        failed = [d for d in DIMENSIONS if d in results and not results[d]]
        ok = not missing and not failed
        return ok, tuple(missing + failed)
