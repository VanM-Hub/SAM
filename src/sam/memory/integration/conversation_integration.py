"""Conversation Integration Bridge — 5 query read-only (Sprint 179)."""
from __future__ import annotations

from ..foundation.memory_registry import MemoryRegistry
from .memory_runtime_pipeline import MemoryRuntimePipeline, INTEGRATION_ROUTE
from .memory_runtime_report import MemoryRuntimeReporter
from .memory_runtime_certification import MemoryRuntimeCertifier


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi memori."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._pipeline = MemoryRuntimePipeline(registry)
        self._reporter = MemoryRuntimeReporter(registry)
        self._certifier = MemoryRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_memories": self._registry.count()}

    def query_3_pipeline(self, memory_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(memory_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_memories, "ready": rep.ready}

    def query_5_certification(self) -> dict:
        """Query 5 — status sertifikasi."""
        c = self._certifier.certify()
        return {"certified": c.certified, "score": c.score}
