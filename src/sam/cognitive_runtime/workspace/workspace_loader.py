"""Workspace Loader — loader workspace read-only (Sprint 192).

Loader HANYA mengembalikan representasi yang sudah ada di memori —
TIDAK membaca disk, TIDAK ada write.
"""
from __future__ import annotations
from dataclasses import dataclass

from .cognitive_workspace import CognitiveWorkspace
from .workspace_catalog import WorkspaceCatalog


@dataclass(frozen=True)
class WorkspaceLoadResult:
    """Hasil load (immutable)."""
    ok: bool = False
    workspace: CognitiveWorkspace | None = None
    detail: str = ""


class WorkspaceLoader:
    """Loader workspace. Read-only (tanpa disk/IO)."""

    def __init__(self, catalog: WorkspaceCatalog) -> None:
        self._catalog = catalog

    def load(self, workspace_id: str) -> WorkspaceLoadResult:
        ws = self._catalog.get(workspace_id)
        if ws is None:
            return WorkspaceLoadResult(ok=False, detail="not found")
        return WorkspaceLoadResult(ok=True, workspace=ws, detail="loaded")
