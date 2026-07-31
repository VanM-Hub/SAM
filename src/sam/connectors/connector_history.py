"""Connector History — engine riwayat monitoring.

Sprint 120 — Connector Monitoring.
Riwayat snapshot (append-only, in-memory).
"""
from __future__ import annotations
from typing import List

from .connector_snapshot import ConnectorSnapshot


class ConnectorHistory:
    """Riwayat snapshot connector."""

    def __init__(self) -> None:
        self._entries: List[ConnectorSnapshot] = []

    def record(self, snapshot: ConnectorSnapshot) -> None:
        self._entries.append(snapshot)

    def all(self) -> List[ConnectorSnapshot]:
        return list(self._entries)

    def by_connector(self, connector_id: str) -> List[ConnectorSnapshot]:
        return [s for s in self._entries if s.connector_id == connector_id]

    def count(self) -> int:
        return len(self._entries)
