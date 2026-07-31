"""Workspace History — riwayat workspace read-only (Sprint 192)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkspaceHistoryEntry:
    """Entri riwayat (immutable)."""
    workspace_id: str = ""
    action: str = "created"
    timestamp: str = ""


class WorkspaceHistory:
    """Riwayat workspace in-memory. Append hanya komposisi (no write)."""

    def __init__(self) -> None:
        self._entries: List[WorkspaceHistoryEntry] = []

    def record(self, entry: WorkspaceHistoryEntry) -> None:
        self._entries.append(entry)

    def all_entries(self) -> List[WorkspaceHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def by_workspace(self, workspace_id: str) -> List[WorkspaceHistoryEntry]:
        return [
            e for e in self._entries if e.workspace_id == workspace_id
        ]
