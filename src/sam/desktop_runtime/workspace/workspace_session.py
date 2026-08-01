"""Sprint 273 - Desktop Workspace: session (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .workspace_model import WorkspaceModel


@dataclass(frozen=True)
class WorkspaceSession:
    """Snapshot session workspace (deklaratif)."""

    session_id: str = "ws-session"
    model: WorkspaceModel = field(default_factory=WorkspaceModel)
    active_panel: str = ""
    panels: Tuple[str, ...] = ()

    def __post_init__(self):
        if self.panels and not self.active_panel:
            object.__setattr__(self, "active_panel", self.panels[0])

    def with_model(self, model: WorkspaceModel) -> "WorkspaceSession":
        return WorkspaceSession(
            session_id=self.session_id,
            model=model,
            active_panel=model.active_panel or self.active_panel,
            panels=self.panels,
        )

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "model": self.model.as_dict(),
            "active_panel": self.active_panel,
            "panels": list(self.panels),
        }
