"""Sprint 273 - Desktop Workspace: dock manager (service, tanpa IO)."""
from __future__ import annotations

from typing import Tuple

from .workspace_state import WorkspaceState


class DockManager:
    """Mengelola susunan dock (service murni, deklaratif, tanpa IO)."""

    @staticmethod
    def dock(state: WorkspaceState, *panels: str) -> WorkspaceState:
        """Dock panel ke workspace (immutable)."""
        merged = tuple(
            dict.fromkeys(state.docked + panels)  # preserve order, dedupe
        )
        visible = tuple(dict.fromkeys(state.visible + panels))
        return WorkspaceState(
            docked=merged,
            floating=state.floating,
            visible=visible,
            dirty=state.dirty,
        )

    @staticmethod
    def float_panel(state: WorkspaceState, panel: str) -> WorkspaceState:
        if panel not in state.docked:
            return state
        docked = tuple(p for p in state.docked if p != panel)
        return WorkspaceState(
            docked=docked,
            floating=state.floating + (panel,),
            visible=state.visible,
            dirty=True,
        )

    @staticmethod
    def close(state: WorkspaceState, panel: str) -> WorkspaceState:
        docked = tuple(p for p in state.docked if p != panel)
        floating = tuple(p for p in state.floating if p != panel)
        visible = tuple(p for p in state.visible if p != panel)
        return WorkspaceState(
            docked=docked,
            floating=floating,
            visible=visible,
            dirty=True,
        )
