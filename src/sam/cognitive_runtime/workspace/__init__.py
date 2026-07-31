"""Cognitive Workspace — workspace kognitif (Phase XIX, Sprint 192)."""
from .cognitive_workspace import CognitiveWorkspace
from .workspace_catalog import WorkspaceCatalog, WorkspaceCatalogEntry
from .workspace_index import WorkspaceIndex, WorkspaceIndexer
from .workspace_loader import WorkspaceLoader, WorkspaceLoadResult
from .workspace_history import WorkspaceHistory, WorkspaceHistoryEntry
from .conversation_workspace import ConversationWorkspaceBridge
from .dashboard_workspace import DashboardWorkspaceBridge

__all__ = [
    "CognitiveWorkspace",
    "WorkspaceCatalog",
    "WorkspaceCatalogEntry",
    "WorkspaceIndex",
    "WorkspaceIndexer",
    "WorkspaceLoader",
    "WorkspaceLoadResult",
    "WorkspaceHistory",
    "WorkspaceHistoryEntry",
    "ConversationWorkspaceBridge",
    "DashboardWorkspaceBridge",
]
