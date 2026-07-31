"""Execution History (Sprint 256).

Program C - Real Execution Runtime.
Riwayat immutable eksekusi. Append-only, no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .execution_report import ExecutionReport


@dataclass(frozen=True)
class ExecutionHistoryEntry:
    """Entri riwayat eksekusi (immutable)."""
    entry_id: str
    execution_id: str
    status: str = "pending"
    provider_id: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"entry_id": self.entry_id, "execution_id": self.execution_id,
                "status": self.status, "provider_id": self.provider_id,
                "external_calls": self.external_calls}


class ExecutionHistory:
    """Riwayat eksekusi. Append-only read-only view."""

    def __init__(self) -> None:
        self._entries: List[ExecutionHistoryEntry] = []

    def record(self, report: ExecutionReport) -> ExecutionHistoryEntry:
        entry = ExecutionHistoryEntry(
            entry_id=f"eh-{len(self._entries) + 1}",
            execution_id=report.execution_id,
            status=report.status,
            external_calls=report.external_calls,
        )
        self._entries.append(entry)
        return entry

    def all(self) -> List[ExecutionHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def find(self, execution_id: str) -> Optional[ExecutionHistoryEntry]:
        for e in self._entries:
            if e.execution_id == execution_id:
                return e
        return None
