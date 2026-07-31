"""Conversation Integration Bridge — 5 query read-only (Sprint 219)."""
from __future__ import annotations

from ..foundation.audit_registry import AuditRegistry
from .audit_runtime_pipeline import AuditRuntimePipeline, INTEGRATION_ROUTE
from .audit_runtime_report import AuditRuntimeReporter
from .audit_runtime_certification import AuditRuntimeCertifier
from .audit_runtime_registry import AuditRuntimeRegistry


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry
        self._pipeline = AuditRuntimePipeline(registry)
        self._reporter = AuditRuntimeReporter(registry)
        self._certifier = AuditRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_audit": self._registry.count()}

    def query_3_pipeline(self, audit_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(audit_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_audit, "ready": rep.ready}

    def query_5_registry(self) -> dict:
        """Query 5 — registry runtime terintegrasi."""
        reg = AuditRuntimeRegistry.from_route(self._pipeline.route())
        return {"count": reg.count, "runtimes": [e.runtime for e in reg.entries]}
