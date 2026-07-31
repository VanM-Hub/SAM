"""Sprint 267 - Certification: report (laporan sertifikasi)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .certifier import Certifier


@dataclass(frozen=True)
class CertificationReport:
    """Laporan immutable hasil sertifikasi."""

    def build(
        self,
        results: Dict[str, bool] | None = None,
        details: Dict[str, str] | None = None,
    ) -> Dict[str, object]:
        certifier = Certifier()
        score, failed, manifest = certifier.certify(results)
        det = dict(details) if details else {}
        return {
            "score": score.as_dict(),
            "failed": list(failed),
            "manifest": manifest.as_dict(),
            "details": det,
        }
