"""Dashboard Integration Bridge — 5 ExecutionCards (Sprint 187)."""
from __future__ import annotations

from ..foundation.knowledge_registry import KnowledgeRegistry
from ..dashboard.knowledge_dashboard import ExecutionCard
from .knowledge_runtime_pipeline import KnowledgeRuntimePipeline
from .knowledge_runtime_certification import KnowledgeRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi knowledge."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._pipeline = KnowledgeRuntimePipeline(registry)
        self._certifier = KnowledgeRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            ExecutionCard("int.route", "integration", "ready",
                          "Mission->Agent->Skill->Memory->Knowledge->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            ExecutionCard("int.knowledge", "integration", "ready",
                          f"{n} knowledge(s) integrated", "read-only", "ready"),
            ExecutionCard("int.preview", "integration", "ready",
                          "execution preview (external_calls=0)", "preview", "ready"),
            ExecutionCard("int.readonly", "integration", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            ExecutionCard("int.cert", "integration", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
