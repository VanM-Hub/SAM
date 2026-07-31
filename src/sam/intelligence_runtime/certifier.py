"""Sprint 267 - Certification: certifier (orchestrator sertifikasi 7 dimensi)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from .manifest import CertificationManifest
from .score import CertificationScore
from .validator import CertificationValidator, DIMENSIONS


@dataclass(frozen=True)
class Certifier:
    """Melakukan sertifikasi 7 dimensi secara deterministik (preview-only)."""

    validator: CertificationValidator = field(
        default_factory=CertificationValidator)

    def certify(
        self,
        results: Dict[str, bool] | None = None,
    ) -> Tuple[CertificationScore, Tuple[str, ...], CertificationManifest]:
        res = dict(results) if results is not None else {d: True for d in DIMENSIONS}
        ok, failed = self.validator.validate(res)
        score = CertificationScore.from_results(res)
        status = "certified" if ok else "failed"
        manifest = CertificationManifest(
            dimensions=tuple(res.keys()), status=status)
        return score, failed, manifest
