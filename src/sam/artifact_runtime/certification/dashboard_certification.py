"""Dashboard Certification Bridge — 5 PolicyCards (Sprint 226)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .artifact_certification import ArtifactCertification


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu sertifikasi artifact."""

    def cards(self):
        res = ArtifactCertification().certify()
        verdict = "certified" if res.certified else "not-certified"
        return [
            PolicyCard("ac.cert", "artifact", verdict,
                       f"score {res.score:.0f}/100", "certification", verdict),
            PolicyCard("ac.7dim", "artifact", "ready",
                       "Structure Integrity Consistency Completeness "
                       "Determinism Immutability PreviewOnly",
                       "certification", "ready"),
            PolicyCard("ac.preview", "artifact", "ready",
                       "no storage / no publish", "certification", "ready"),
            PolicyCard("ac.noexecute", "artifact", "ready",
                       "representation only", "certification", "ready"),
            PolicyCard("ac.deterministic", "artifact", "ready",
                       "deterministic certified", "certification", "ready"),
        ]
