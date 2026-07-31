"""Workspace Catalog — katalog workspace read-only (Sprint 192)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .cognitive_workspace import CognitiveWorkspace


@dataclass(frozen=True)
class WorkspaceCatalogEntry:
    """Entri katalog (immutable)."""
    workspace_id: str
    item_count: int = 0


class WorkspaceCatalog:
    """Katalog workspace in-memory. Register hanya komposisi (no write)."""

    def __init__(self) -> None:
        self._workspaces = {}

    def add(self, workspace: CognitiveWorkspace) -> None:
        self._workspaces[workspace.workspace_id] = workspace

    def get(self, workspace_id: str) -> CognitiveWorkspace | None:
        return self._workspaces.get(workspace_id)

    def all_entries(self) -> List[WorkspaceCatalogEntry]:
        return [
            WorkspaceCatalogEntry(workspace_id=ws.workspace_id, item_count=ws.item_count())
            for ws in self._workspaces.values()
        ]

    def count(self) -> int:
        return len(self._workspaces)
