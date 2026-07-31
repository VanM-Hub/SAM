"""Conversation Integration Bridge — 5 query read-only (Sprint 187)."""
from __future__ import annotations

from ..foundation.knowledge_registry import KnowledgeRegistry
from .knowledge_runtime_pipeline import KnowledgeRuntimePipeline, INTEGRATION_ROUTE
from .knowledge_runtime_report import KnowledgeRuntimeReporter
from .knowledge_runtime_certification import KnowledgeRuntimeCertifier


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi knowledge."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._pipeline = KnowledgeRuntimePipeline(registry)
        self._reporter = KnowledgeRuntimeReporter(registry)
        self._certifier = KnowledgeRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_knowledge": self._registry.count()}

    def query_3_pipeline(self, knowledge_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(knowledge_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_knowledge, "ready": rep.ready}

    def query_5_certification(self) -> dict:
        """Query 5 — status sertifikasi."""
        c = self._certifier.certify()
        return {"certified": c.certified, "score": c.score}
