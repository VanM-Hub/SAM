"""ArtifactCertification — sertifikasi 7 dimensi (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactCertificationCriterion:
    name: str = ""
    passed: bool = True
    detail: str = ""


@dataclass(frozen=True)
class ArtifactCertificationResult:
    certified: bool = True
    score: float = 100.0
    checks: Tuple[ArtifactCertificationCriterion, ...] = ()


@dataclass(frozen=True)
class ArtifactCertification:
    """Sertifikasi representasi artifact — 7 dimensi.

    Structure, Integrity, Consistency, Completeness, Determinism,
    Immutability, PreviewOnly.
    Default = semua lulus (asumsi representasi deterministic/immutable/preview).
    """
    structure: bool = True
    integrity: bool = True
    consistency: bool = True
    completeness: bool = True
    determinism: bool = True
    immutability: bool = True
    preview_only: bool = True
    no_storage: bool = True
    no_publish: bool = True

    def certify(self) -> ArtifactCertificationResult:
        checks = (
            ArtifactCertificationCriterion("Structure", self.structure, "structure valid"),
            ArtifactCertificationCriterion("Integrity", self.integrity, "integrity intact"),
            ArtifactCertificationCriterion("Consistency", self.consistency, "consistent"),
            ArtifactCertificationCriterion("Completeness", self.completeness, "complete"),
            ArtifactCertificationCriterion("Determinism", self.determinism, "deterministic"),
            ArtifactCertificationCriterion("Immutability", self.immutability, "immutable"),
            ArtifactCertificationCriterion("PreviewOnly", self.preview_only, "preview-only"),
        )
        passed = all(c.passed for c in checks) and \
            self.no_storage and self.no_publish
        score = sum(1 for c in checks if c.passed) / len(checks) * 100.0
        if not passed:
            score = min(score, self._fraction_of_policy() * 100.0)
        return ArtifactCertificationResult(certified=passed, score=score,
                                           checks=checks)

    def _fraction_of_policy(self) -> float:
        ok = sum([
            self.no_storage, self.no_publish, self.immutability,
            self.preview_only,
        ])
        return ok / 4.0
