"""Dashboard Workspace Bridge — 5 ExecutionCards (Sprint 192)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from .cognitive_workspace import CognitiveWorkspace
from .workspace_catalog import WorkspaceCatalog
from .workspace_loader import WorkspaceLoader


class DashboardWorkspaceBridge:
    """Bridge dashboard — 5 kartu untuk workspace kognitif."""

    def __init__(self, catalog: WorkspaceCatalog = None) -> None:
        self._catalog = catalog or WorkspaceCatalog()
        self._loader = WorkspaceLoader(self._catalog)

    def cards(self, workspace: CognitiveWorkspace = None):
        ws = workspace or CognitiveWorkspace("w0")
        return [
            ExecutionCard("wk.workspace", "workspace", "ready",
                          f"{ws.workspace_id} ({ws.item_count()} items)",
                          "workspace", "ready"),
            ExecutionCard("wk.catalog", "workspace", "ready",
                          f"{self._catalog.count()} workspace(s) catalogued",
                          "catalog", "ready"),
            ExecutionCard("wk.index", "workspace", "ready",
                          "WorkspaceIndex frozen (tuple items)", "index", "ready"),
            ExecutionCard("wk.no_write", "workspace", "ready",
                          "workspace: immutable, NO write", "preview", "ready"),
            ExecutionCard("wk.history", "workspace", "ready",
                          "WorkspaceHistory read-only", "history", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
