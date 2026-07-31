"""Conversation Integration Bridge — 5 read-only queries (Sprint 227)."""
from __future__ import annotations

from ..foundation.artifact_registry import ArtifactRegistry
from .artifact_runtime_pipeline import ArtifactRuntimePipeline, INTEGRATION_ROUTE
from .artifact_runtime_report import ArtifactRuntimeReporter
from .artifact_runtime_summary import ArtifactRuntimeSummarizer
from .artifact_runtime_registry import ArtifactRuntimeRegistry


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query integrasi artifact."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry
        self._pipeline = ArtifactRuntimePipeline(registry)
        self._reporter = ArtifactRuntimeReporter(registry)
        self._summarizer = ArtifactRuntimeSummarizer()

    def query_1_route(self):
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        return {"total_artifact": self._registry.count()}

    def query_3_pipeline(self, name: str) -> dict:
        run = self._pipeline.run(name)
        return {"ok": run.ok, "external_calls": run.external_calls,
                "stages": len(run.stages)}

    def query_4_report(self) -> dict:
        rep = self._reporter.report()
        return {"total": rep.total_artifact, "ready": rep.ready,
                "no_storage": rep.no_storage}

    def query_5_registry(self) -> dict:
        reg = ArtifactRuntimeRegistry.from_route(self._pipeline.route())
        return {"count": reg.count,
                "runtimes": [e.runtime for e in reg.entries]}
