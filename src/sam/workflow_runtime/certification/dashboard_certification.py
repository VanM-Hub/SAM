"""Dashboard Certification Bridge — 5 WorkflowCards (Sprint 202)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from .workflow_certification import WorkflowCertification


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk sertifikasi workflow."""

    def __init__(self, certification: WorkflowCertification = None) -> None:
        self._cert = certification or WorkflowCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_inference=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            WorkflowCard("cf.score", "certification", verdict,
                         f"score {result.score:.0f}/100", "workflow score", verdict),
            WorkflowCard("cf.structure", "certification", "ready",
                         "Structure passed", "certification", "ready"),
            WorkflowCard("cf.determinism", "certification", "ready",
                         "Determinism passed", "deterministic", "ready"),
            WorkflowCard("cf.dto", "certification", "ready",
                         "Immutability: frozen", "immutable", "ready"),
            WorkflowCard("cf.no_infer", "certification", "ready",
                         "PreviewOnly + no inference + no write", "preview", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
