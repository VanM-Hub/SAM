"""Conversation Integration Bridge — 5 query read-only (Sprint 203)."""
from __future__ import annotations

from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_runtime_pipeline import WorkflowRuntimePipeline, INTEGRATION_ROUTE
from .workflow_runtime_report import WorkflowRuntimeReporter
from .workflow_runtime_certification import WorkflowRuntimeCertifier
from .workflow_runtime_registry import WorkflowRuntimeRegistry


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._pipeline = WorkflowRuntimePipeline(registry)
        self._reporter = WorkflowRuntimeReporter(registry)
        self._certifier = WorkflowRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_workflow": self._registry.count()}

    def query_3_pipeline(self, workflow_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(workflow_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_workflow, "ready": rep.ready}

    def query_5_registry(self) -> dict:
        """Query 5 — registry runtime terintegrasi."""
        reg = WorkflowRuntimeRegistry.from_route(self._pipeline.route())
        return {"count": reg.count, "runtimes": [e.runtime for e in reg.entries]}
