"""Workflow History — riwayat workflow read-only (Sprint 200)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowHistoryEntry:
    """Entri riwayat (immutable)."""
    workflow_id: str = ""
    action: str = "created"
    timestamp: str = ""


class WorkflowHistory:
    """Riwayat workflow in-memory. Append hanya komposisi (no write)."""

    def __init__(self) -> None:
        self._entries: List[WorkflowHistoryEntry] = []

    def record(self, entry: WorkflowHistoryEntry) -> None:
        self._entries.append(entry)

    def all_entries(self) -> List[WorkflowHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def by_workflow(self, workflow_id: str) -> List[WorkflowHistoryEntry]:
        return [
            e for e in self._entries if e.workflow_id == workflow_id
        ]
