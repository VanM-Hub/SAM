"""ArtifactCertificationValidator — validasi sertifikasi (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactCertificationValidation:
    valid: bool = True
    checks: tuple = ()


class ArtifactCertificationValidator:
    """Validator hasil sertifikasi. Deterministic & read-only."""

    def validate(self, result) -> ArtifactCertificationValidation:
        certified = getattr(result, "certified", True)
        external_calls = getattr(result, "external_calls", 0) or \
            getattr(getattr(result, "report", None), "external_calls", 0)
        check = certified and external_calls == 0
        return ArtifactCertificationValidation(
            valid=check,
            checks=(("certified", certified), ("external_calls_zero",
                                               external_calls == 0)),
        )
