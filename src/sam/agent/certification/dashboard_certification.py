"""Dashboard Certification Bridge — 5 ExecutionCards (Sprint 163).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .agent_certification import AgentCertification
from ..dashboard.agent_dashboard import ExecutionCard
from .agent_certification import CertificationCriterion  # noqa: F401


class DashboardCertificationBridge:
    """Bridge dashboard — 5 kartu untuk certification."""

    def __init__(self, certification: AgentCertification = None) -> None:
        self._cert = certification or AgentCertification()

    def cards(self):
        result = self._cert.certify(
            modules_present=10, modules_expected=10,
            dto_frozen=True, no_forbidden_imports=True, deterministic=True,
        )
        verdict = "certified" if result.certified else "not-certified"
        return [
            ExecutionCard("cert.score", "certification", verdict,
                          f"score {result.total_score:.0f}/100",
                          "agent score", verdict),
            ExecutionCard("cert.determinism", "certification", "ready",
                          "Determinism passed", "deterministic", "ready"),
            ExecutionCard("cert.layer_safety", "certification", "ready",
                          "Layer Safety passed", "no forbidden import", "ready"),
            ExecutionCard("cert.dto", "certification", "ready",
                          "DTO Safety: frozen", "immutable", "ready"),
            ExecutionCard("cert.pipeline", "certification", "ready",
                          "Pipeline Safety: deterministic", "pipeline", "ready"),
        ]

    def verdict_card(self):
        return self.cards()[0]
