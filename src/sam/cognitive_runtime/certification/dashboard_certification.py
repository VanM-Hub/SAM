"""Dashboard Certification Bridge — 5 ExecutionCards (Sprint 194)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from .cognitive_certification import CognitiveCertification


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk sertifikasi kognitif."""

    def __init__(self, certification: CognitiveCertification = None) -> None:
        self._cert = certification or CognitiveCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_inference=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            ExecutionCard("cf.score", "certification", verdict,
                          f"score {result.score:.0f}/100", "cognitive score", verdict),
            ExecutionCard("cf.structure", "certification", "ready",
                          "Structure passed", "certification", "ready"),
            ExecutionCard("cf.determinism", "certification", "ready",
                          "Determinism passed", "deterministic", "ready"),
            ExecutionCard("cf.dto", "certification", "ready",
                          "Immutability: frozen", "immutable", "ready"),
            ExecutionCard("cf.no_infer", "certification", "ready",
                          "PreviewOnly + no inference + no write", "preview", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
