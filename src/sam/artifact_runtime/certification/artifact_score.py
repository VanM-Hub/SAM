"""ArtifactScore — skor sertifikasi artifact (duck typing, no circular import)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactCertificationDimension:
    name: str = ""
    score: float = 100.0


@dataclass(frozen=True)
class ArtifactScore:
    """Skor sertifikasi artifact. Immutable."""
    score: float = 100.0
    certified: bool = True


class ArtifactScorer:
    """Penghitung skor. Menerima object hasil `certify()` (duck typing)."""

    def score(self, result) -> ArtifactScore:
        # result: objeck dengan certified + score (misal ArtifactCertificationResult)
        certified = getattr(result, "certified", True)
        score = getattr(result, "score", 100.0)
        return ArtifactScore(score=score, certified=certified)
