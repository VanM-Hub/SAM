"""OpenClaw Tool History — riwayat preview tool (read-only).

Sprint 149 — OpenClaw Provider.
Mencatat riwayat preview tool. Tidak ada invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class OpenClawHistoryEntry:
    """Satu entri riwayat preview tool (immutable)."""
    request_id: str
    tool: str
    invoked: bool = False
    external_calls: int = 0


class OpenClawToolHistory:
    """Riwayat preview tool. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[OpenClawHistoryEntry] = []

    def record(self, entry: OpenClawHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[OpenClawHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def total_external_calls(self) -> int:
        return sum(e.external_calls for e in self._entries)
