"""Binding History — engine riwayat binding.

Sprint 115 — Connector Binding.
Riwayat binding (append-only, in-memory). Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .binding_result import BindingResult


@dataclass(frozen=True)
class BindingHistoryEntry:
    """Entri riwayat binding (immutable)."""
    binding_id: str
    connector_id: str
    status: str = "bound"
    timestamp_iso: str = ""


class BindingHistory:
    """Riwayat binding connector."""

    def __init__(self) -> None:
        self._entries: List[BindingHistoryEntry] = []

    def record(self, result: BindingResult, timestamp_iso: str = "") -> None:
        self._entries.append(BindingHistoryEntry(
            result.binding_id, result.connector_id,
            "bound" if result.success else "failed", timestamp_iso,
        ))

    def all(self) -> List[BindingHistoryEntry]:
        return list(self._entries)

    def by_connector(self, connector_id: str) -> List[BindingHistoryEntry]:
        return [e for e in self._entries if e.connector_id == connector_id]

    def count(self) -> int:
        return len(self._entries)
