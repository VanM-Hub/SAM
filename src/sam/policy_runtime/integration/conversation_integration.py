"""Conversation Integration Bridge — 5 query read-only (Sprint 211)."""
from __future__ import annotations

from ..foundation.policy_registry import PolicyRegistry
from .policy_runtime_pipeline import PolicyRuntimePipeline, INTEGRATION_ROUTE
from .policy_runtime_report import PolicyRuntimeReporter
from .policy_runtime_certification import PolicyRuntimeCertifier
from .policy_runtime_registry import PolicyRuntimeRegistry


class ConversationIntegrationBridge:
    """Bridge conversation — 5 query read-only integrasi policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._pipeline = PolicyRuntimePipeline(registry)
        self._reporter = PolicyRuntimeReporter(registry)
        self._certifier = PolicyRuntimeCertifier()

    def query_1_route(self) -> list:
        """Query 1 — rute pipeline integrasi."""
        return self._pipeline.route()

    def query_2_status(self) -> dict:
        """Query 2 — status registry."""
        return {"total_policy": self._registry.count()}

    def query_3_pipeline(self, policy_id: str) -> dict:
        """Query 3 — jalankan pipeline preview (read-only)."""
        run = self._pipeline.run(policy_id)
        return {"ok": run.ok, "external_calls": run.external_calls}

    def query_4_report(self) -> dict:
        """Query 4 — laporan runtime."""
        rep = self._reporter.report()
        return {"total": rep.total_policy, "ready": rep.ready}

    def query_5_registry(self) -> dict:
        """Query 5 — registry runtime terintegrasi."""
        reg = PolicyRuntimeRegistry.from_route(self._pipeline.route())
        return {"count": reg.count, "runtimes": [e.runtime for e in reg.entries]}
