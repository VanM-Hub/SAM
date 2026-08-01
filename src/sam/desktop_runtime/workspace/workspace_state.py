"""Sprint 273 - Desktop Workspace: state (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class WorkspaceState:
    """State workspace read-only (deterministik, tanpa IO)."""

    docked: Tuple[str, ...] = ()
    floating: Tuple[str, ...] = ()
    visible: Tuple[str, ...] = ()
    dirty: bool = False

    def with_docked(self, *panels: str) -> "WorkspaceState":
        return WorkspaceState(
            docked=self.docked + tuple(panels),
            floating=self.floating,
            visible=self.visible + tuple(panels),
            dirty=self.dirty,
        )

    def mark_dirty(self) -> "WorkspaceState":
        return WorkspaceState(
            docked=self.docked,
            floating=self.floating,
            visible=self.visible,
            dirty=True,
        )

    def as_dict(self) -> dict:
        return {
            "docked": list(self.docked),
            "floating": list(self.floating),
            "visible": list(self.visible),
            "dirty": self.dirty,
        }
