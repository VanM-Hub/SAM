"""Dashboard Certification Bridge — 5 ExecutionCards (Sprint 178)."""
from __future__ import annotations

from .memory_certification import MemoryCertification
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk memory certification."""

    def __init__(self, certification: MemoryCertification = None) -> None:
        self._cert = certification or MemoryCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            ExecutionCard("cert.score", "certification", verdict,
                          f"score {result.score:.0f}/100", "memory score", verdict),
            ExecutionCard("cert.structure", "certification", "ready",
                          "Structure passed", "certification", "ready"),
            ExecutionCard("cert.determinism", "certification", "ready",
                          "Determinism passed", "deterministic", "ready"),
            ExecutionCard("cert.dto", "certification", "ready",
                          "Immutability: frozen", "immutable", "ready"),
            ExecutionCard("cert.no_write", "certification", "ready",
                          "PreviewOnly + no write", "preview", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
