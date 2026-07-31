"""Preview History — engine riwayat preview.

Sprint 119 — Connector Preview.
Riwayat preview (append-only, in-memory). Tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .preview_result import PreviewResult


@dataclass(frozen=True)
class PreviewHistoryEntry:
    """Entri riwayat preview (immutable)."""
    preview_id: str
    connector_id: str
    operation: str = "read"
    success: bool = False


class PreviewHistory:
    """Riwayat preview connector."""

    def __init__(self) -> None:
        self._entries: List[PreviewHistoryEntry] = []

    def record(self, result: PreviewResult) -> None:
        self._entries.append(PreviewHistoryEntry(
            result.preview_id, result.connector_id, result.operation, result.success,
        ))

    def all(self) -> List[PreviewHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)
