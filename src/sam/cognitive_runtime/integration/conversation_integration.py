"""Conversation Integration Bridge — 5 query read-only (Sprint 195)."""
from __future__ import annotations

from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_runtime_pipeline import CognitiveRuntimePipeline, INTEGRATION_ROUTE
from .cognitive_runtime_report import CognitiveRuntimeReporter
from .cognitive_runtime_certification import CognitiveRuntimeCertifier


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._pipeline = CognitiveRuntimePipeline(registry)
        self._reporter = CognitiveRuntimeReporter(registry)
        self._certifier = CognitiveRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_cognitive": self._registry.count()}

    def query_3_pipeline(self, cognitive_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(cognitive_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_cognitive, "ready": rep.ready}

    def query_5_certification(self) -> dict:
        """Query 5 — status sertifikasi."""
        c = self._certifier.certify()
        return {"certified": c.certified, "score": c.score}
