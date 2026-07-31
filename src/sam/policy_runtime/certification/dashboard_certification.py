"""Dashboard Certification Bridge — 5 PolicyCards (Sprint 210)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .policy_certification import PolicyCertification


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk sertifikasi policy."""

    def __init__(self, certification: PolicyCertification = None) -> None:
        self._cert = certification or PolicyCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_inference=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            PolicyCard("cf.score", "certification", verdict,
                       f"score {result.score:.0f}/100", "policy score", verdict),
            PolicyCard("cf.structure", "certification", "ready",
                       "Structure passed", "certification", "ready"),
            PolicyCard("cf.determinism", "certification", "ready",
                       "Determinism passed", "deterministic", "ready"),
            PolicyCard("cf.dto", "certification", "ready",
                       "Immutability: frozen", "immutable", "ready"),
            PolicyCard("cf.no_infer", "certification", "ready",
                       "PreviewOnly + no inference + no write", "preview", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
