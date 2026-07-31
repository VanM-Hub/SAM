"""Conversation Capability — bridge read-only untuk kapabilitas.

Sprint 114 — Connector Capability.
Query read-only. Tidak ada mutasi.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .capability_report import CapabilityReport, CapabilityReporter
from .capability_matrix import CapabilityMatrix


class ConversationCapabilityBridge:
    """Bridge conversation capability — read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._reporter = CapabilityReporter(registry)

    def get_report(self, connector_id: str) -> CapabilityReport:
        return self._reporter.report(connector_id)

    def matrix(self) -> CapabilityMatrix:
        from .capability_matrix import CapabilityMatrixBuilder
        return CapabilityMatrixBuilder(self._registry).build()

    def list_capabilities(self, connector_id: str) -> List[str]:
        return self._reporter.report(connector_id).capability_names
