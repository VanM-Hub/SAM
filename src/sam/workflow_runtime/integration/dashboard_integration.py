"""Dashboard Integration Bridge — 5 WorkflowCards (Sprint 203)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_runtime_pipeline import WorkflowRuntimePipeline
from .workflow_runtime_certification import WorkflowRuntimeCertifier


class DashboardIntegrationBridge:
    """Bridge dashboard — 5 kartu untuk integrasi workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._pipeline = WorkflowRuntimePipeline(registry)
        self._certifier = WorkflowRuntimeCertifier()

    def cards(self):
        n = self._registry.count()
        cert = self._certifier.certify()
        verdict = "certified" if cert.certified else "not-certified"
        return [
            WorkflowCard("ig.route", "integration", "ready",
                          "Mission->Agent->Skill->Workflow->Memory->Knowledge->Cognitive->Orchestrator->Connector->Provider",
                          "pipeline", "ready"),
            WorkflowCard("ig.workflow", "integration", "ready",
                          f"{n} workflow(s) integrated", "read-only", "ready"),
            WorkflowCard("ig.preview", "integration", "ready",
                          "execution preview (external_calls=0)", "preview", "ready"),
            WorkflowCard("ig.readonly", "integration", "ready",
                          "0 layer violations - runtime lain tak diubah",
                          "integration", "ready"),
            WorkflowCard("ig.cert", "integration", verdict,
                          f"score {cert.score:.0f}/100", "certification", verdict),
        ]

    def verdict_card(self):
        return self.cards()[4]
