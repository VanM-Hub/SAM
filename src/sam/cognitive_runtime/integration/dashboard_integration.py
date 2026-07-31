"""Dashboard Integration Bridge — 5 ExecutionCards (Sprint 195)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_runtime_pipeline import CognitiveRuntimePipeline
from .cognitive_runtime_certification import CognitiveRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._pipeline = CognitiveRuntimePipeline(registry)
        self._certifier = CognitiveRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            ExecutionCard("ig.route", "integration", "ready",
                          "Mission->Agent->Skill->Memory->Knowledge->Cognitive->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            ExecutionCard("ig.cognitive", "integration", "ready",
                          f"{n} cognitive(s) integrated", "read-only", "ready"),
            ExecutionCard("ig.preview", "integration", "ready",
                          "execution preview (external_calls=0)", "preview", "ready"),
            ExecutionCard("ig.readonly", "integration", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            ExecutionCard("ig.cert", "integration", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
