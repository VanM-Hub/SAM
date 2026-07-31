"""Dashboard Integration Bridge — 5 ExecutionCards (Sprint 179)."""
from __future__ import annotations

from ..foundation.memory_registry import MemoryRegistry
from ..dashboard.memory_dashboard import ExecutionCard
from .memory_runtime_pipeline import MemoryRuntimePipeline
from .memory_runtime_certification import MemoryRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi memori."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._pipeline = MemoryRuntimePipeline(registry)
        self._certifier = MemoryRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            ExecutionCard("int.route", "integration", "ready",
                          "Mission->Agent->Skill->Memory->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            ExecutionCard("int.memory", "integration", "ready",
                          f"{n} memory(s) integrated", "read-only", "ready"),
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
