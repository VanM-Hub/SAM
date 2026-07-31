"""Conversation Runtime — bridge read-only untuk connector runtime.

Sprint 121 — Connector Runtime.
Query read-only ke runtime coordinator. Tidak ada mutasi.
"""
from __future__ import annotations

from .connector_registry import ConnectorRegistry
from .runtime_coordinator import RuntimeCoordinator
from .runtime import RuntimeReadiness
from .runtime_report import RuntimeReport, RuntimeReporter


class ConversationRuntimeBridge:
    """Bridge conversation runtime — read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._coordinator = RuntimeCoordinator(registry)
        from .runtime import ConnectorRuntime
        self._reporter = RuntimeReporter(ConnectorRuntime(registry))

    def readiness(self) -> RuntimeReadiness:
        return self._coordinator.readiness()

    def report(self) -> RuntimeReport:
        return self._reporter.report()
