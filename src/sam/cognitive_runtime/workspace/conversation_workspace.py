"""Conversation Workspace Bridge — 5 query read-only (Sprint 192)."""
from __future__ import annotations

from .cognitive_workspace import CognitiveWorkspace
from .workspace_catalog import WorkspaceCatalog
from .workspace_index import WorkspaceIndexer
from .workspace_loader import WorkspaceLoader
from .workspace_history import WorkspaceHistory, WorkspaceHistoryEntry


class ConversationWorkspaceBridge:
    """Bridge conversation — 5 query read-only workspace."""

    def __init__(self, catalog: WorkspaceCatalog = None) -> None:
        self._catalog = catalog or WorkspaceCatalog()
        self._loader = WorkspaceLoader(self._catalog)
        self._indexer = WorkspaceIndexer()
        self._history = WorkspaceHistory()

    def query_1_add(self, workspace: CognitiveWorkspace) -> dict:
        self._catalog.add(workspace)
        self._history.record(WorkspaceHistoryEntry(
            workspace_id=workspace.workspace_id, action="created",
        ))
        return {"added": workspace.workspace_id, "count": self._catalog.count()}

    def query_2_load(self, workspace_id: str) -> dict:
        r = self._loader.load(workspace_id)
        return {"ok": r.ok, "detail": r.detail}

    def query_3_index(self, workspace_id: str) -> dict:
        ws = self._catalog.get(workspace_id)
        if ws is None:
            return {"ok": False}
        idx = self._indexer.index(ws)
        return {"ok": True, "item_count": idx.item_count}

    def query_4_search(self, workspace_id: str, term: str) -> list:
        ws = self._catalog.get(workspace_id)
        if ws is None:
            return []
        idx = self._indexer.index(ws)
        return self._indexer.search(idx, term)

    def query_5_history(self, workspace_id: str) -> list:
        return [e.workspace_id for e in self._history.by_workspace(workspace_id)]
