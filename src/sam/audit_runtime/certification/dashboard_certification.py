"""Dashboard Certification Bridge — 5 PolicyCards (Sprint 218)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .audit_certification import AuditCertification


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu sertifikasi audit."""

    def cards(self):
        r = AuditCertification().certify()
        verdict = "certified" if r.certified else "not-certified"
        return [
            PolicyCard("ac.ert.cert", "audit", verdict,
                          f"score {r.score:.0f}/100",
                          "certification", verdict),
            PolicyCard("ac.ert.structure", "audit", "ready",
                          "Structure (9 modules aligned)",
                          "certification", "ready"),
            PolicyCard("ac.ert.immutable", "audit", "immutable",
                          "Immutability (frozen DTO)",
                          "certification", "immutable"),
            PolicyCard("ac.ert.determinism", "audit", "ready",
                          "Determinism (no inference)",
                          "certification", "ready"),
            PolicyCard("ac.ert.preview", "audit", "preview_only",
                          "PreviewOnly (no write, no execute)",
                          "certification", "preview_only"),
        ]

    def verdict_card(self):
        return self.cards()[0]
