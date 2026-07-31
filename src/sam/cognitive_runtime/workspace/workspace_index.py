"""Workspace Index — indeks item workspace (Sprint 192)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .cognitive_workspace import CognitiveWorkspace


@dataclass(frozen=True)
class WorkspaceIndex:
    """Indeks workspace (immutable)."""
    workspace_id: str = ""
    item_count: int = 0
    items: tuple = ()

    def has(self, item: str) -> bool:
        return item in self.items


class WorkspaceIndexer:
    """Indexer workspace. Read-only, deterministik."""

    def index(self, workspace: CognitiveWorkspace) -> WorkspaceIndex:
        return WorkspaceIndex(
            workspace_id=workspace.workspace_id,
            item_count=workspace.item_count(),
            items=tuple(workspace.items),
        )

    def search(self, index: WorkspaceIndex, term: str) -> List[str]:
        return [item for item in index.items if term in item]
