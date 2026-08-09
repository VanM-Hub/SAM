"""Unified Workspace - WP-01 (MISSION-4.6 / IP-4.6-001).

Workspace terpadu sebagai pintu masuk seluruh capability Platform. Workspace
mempertahankan state sesi, TIDAK memiliki logic domain, dan hanya mengonsumsi
capability melalui API.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class WorkspaceMetadata:
    """Metadata workspace."""

    workspace_id: str
    name: str
    created_at: str = field(default_factory=_now_utc)
    version: str = "1.0"

    def as_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "created_at": self.created_at,
            "version": self.version,
        }


@dataclass(frozen=True)
class WorkspaceLayout:
    """Layout workspace (panels/view regions)."""

    panels: Tuple[str, ...] = (
        "overview",
        "citizens",
        "runtimes",
        "providers",
        "context",
        "activity",
    )

    def as_dict(self) -> dict:
        return {"panels": list(self.panels)}


@dataclass(frozen=True)
class WorkspaceConfiguration:
    """Konfigurasi workspace."""

    default_panel: str = "overview"
    theme: str = "light"
    refresh_interval: int = 30  # seconds

    def as_dict(self) -> dict:
        return {
            "default_panel": self.default_panel,
            "theme": self.theme,
            "refresh_interval": self.refresh_interval,
        }


@dataclass(frozen=True)
class WorkspaceState:
    """State workspace aktif (session)."""

    workspace_id: str
    active_panel: str = "overview"
    active_entity_id: str = ""
    navigation_stack: Tuple[str, ...] = field(default_factory=tuple)
    updated_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "active_panel": self.active_panel,
            "active_entity_id": self.active_entity_id,
            "navigation_stack": list(self.navigation_stack),
            "updated_at": self.updated_at,
        }


class WorkspaceNavigation:
    """Navigasi workspace (stack-based, immutable state)."""

    @staticmethod
    def navigate(
        state: WorkspaceState, panel: str, entity_id: str = ""
    ) -> WorkspaceState:
        return WorkspaceState(
            workspace_id=state.workspace_id,
            active_panel=panel,
            active_entity_id=entity_id,
            navigation_stack=state.navigation_stack + (panel,),
        )

    @staticmethod
    def back(state: WorkspaceState) -> WorkspaceState:
        if not state.navigation_stack:
            return state
        stack = state.navigation_stack[:-1]
        return WorkspaceState(
            workspace_id=state.workspace_id,
            active_panel=stack[-1] if stack else "overview",
            active_entity_id="",
            navigation_stack=stack,
        )


class UnifiedWorkspace:
    """Pintu masuk capability (tanpa logic domain)."""

    def __init__(self, name: str = "SAM Operational Workspace") -> None:
        self.metadata = WorkspaceMetadata(
            workspace_id=uuid.uuid4().hex, name=name
        )
        self.layout = WorkspaceLayout()
        self.configuration = WorkspaceConfiguration()
        self._state = WorkspaceState(workspace_id=self.metadata.workspace_id)

    @property
    def state(self) -> WorkspaceState:
        return self._state

    def show(self, panel: str, entity_id: str = "") -> WorkspaceState:
        self._state = WorkspaceNavigation.navigate(
            self._state, panel, entity_id
        )
        return self._state

    def back(self) -> WorkspaceState:
        self._state = WorkspaceNavigation.back(self._state)
        return self._state

    def as_dict(self) -> dict:
        return {
            "metadata": self.metadata.as_dict(),
            "layout": self.layout.as_dict(),
            "configuration": self.configuration.as_dict(),
            "state": self._state.as_dict(),
        }
