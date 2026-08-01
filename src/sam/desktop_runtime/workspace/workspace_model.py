"""Sprint 273 - Desktop Workspace: workspace model (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class WorkspaceModel:
    """Model workspace desktop (murni deklaratif, tanpa state mutabel)."""

    workspace_id: str = "main"
    name: str = "Main Workspace"
    layout: str = "default"
    panels: Tuple[str, ...] = ()
    active_panel: str = ""

    def with_panels(self, *panels: str) -> "WorkspaceModel":
        return WorkspaceModel(
            workspace_id=self.workspace_id,
            name=self.name,
            layout=self.layout,
            panels=self.panels + tuple(panels),
            active_panel=self.active_panel,
        )

    def with_active(self, panel: str) -> "WorkspaceModel":
        return WorkspaceModel(
            workspace_id=self.workspace_id,
            name=self.name,
            layout=self.layout,
            panels=self.panels,
            active_panel=panel,
        )

    def as_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "layout": self.layout,
            "panels": list(self.panels),
            "active_panel": self.active_panel,
        }
