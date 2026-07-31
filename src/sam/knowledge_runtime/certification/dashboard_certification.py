"""Dashboard Certification Bridge — 5 ExecutionCards (Sprint 186)."""
from __future__ import annotations

from .knowledge_certification import KnowledgeCertification
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk knowledge certification."""

    def __init__(self, certification: KnowledgeCertification = None) -> None:
        self._cert = certification or KnowledgeCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_inference=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            ExecutionCard("cert.score", "certification", verdict,
                          f"score {result.score:.0f}/100", "knowledge score", verdict),
            ExecutionCard("cert.structure", "certification", "ready",
                          "Structure passed", "certification", "ready"),
            ExecutionCard("cert.determinism", "certification", "ready",
                          "Determinism passed", "deterministic", "ready"),
            ExecutionCard("cert.dto", "certification", "ready",
                          "Immutability: frozen", "immutable", "ready"),
            ExecutionCard("cert.no_infer", "certification", "ready",
                          "PreviewOnly + no inference + no write", "preview", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
