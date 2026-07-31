"""Conversation Connector — bridge read-only untuk konsumsi internal.

Sprint 112 — Connector Foundation.
Mengakses registry secara read-only. Tidak memodifikasi apa pun.
"""
from __future__ import annotations
from typing import List, Optional

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor, ConnectorSummary


class ConversationConnectorBridge:
    """Bridge conversation — query read-only ke ConnectorRegistry.

    Tidak ada mutasi state. Semua metode hanya membaca.
    """

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def describe(self, level: str = "basic") -> ConnectorSummary:
        """Ringkasan connector terdaftar."""
        return self._registry.summary()

    def list_connectors(self) -> List[str]:
        """Daftar connector id."""
        return self._registry.list_ids()

    def get(self, connector_id: str) -> Optional[ConnectorDescriptor]:
        """Ambil descriptor connector."""
        return self._registry.get(connector_id)

    def count_connectors(self) -> int:
        """Jumlah connector terdaftar."""
        return self._registry.count()
