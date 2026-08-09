"""Workspace API - WP-07 (MISSION-4.6 / IP-4.6-001).

Antarmuka terpadu untuk seluruh Workspace. API konsisten, hanya mengonsumsi
capability, tidak memiliki dependency langsung ke implementasi domain.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .workspace import UnifiedWorkspace
from .operational_session import SessionManager
from .explorers import (
    CitizenExplorer,
    ProviderExplorer,
    RuntimeExplorer,
)
from .operational_context import ContextManager


class WorkspaceAPI:
    """Facade terpadu (hanya konsumsi capability, tanpa logic domain)."""

    def __init__(
        self,
        *,
        workspace: UnifiedWorkspace,
        sessions: SessionManager,
        citizens: CitizenExplorer,
        runtimes: RuntimeExplorer,
        providers: ProviderExplorer,
        context: ContextManager,
    ) -> None:
        self._workspace = workspace
        self._sessions = sessions
        self._citizens = citizens
        self._runtimes = runtimes
        self._providers = providers
        self._context = context

    # --- Workspace / Navigation ---
    def overview(self) -> Dict[str, Any]:
        return self._workspace.as_dict()

    def navigate(self, panel: str, entity_id: str = "") -> Dict[str, Any]:
        return self._workspace.show(panel, entity_id).as_dict()

    # --- Session ---
    def create_session(self, user: str = "") -> Dict[str, Any]:
        session = self._sessions.create(
            user=user, workspace_id=self._workspace.metadata.workspace_id
        )
        return session.as_dict()

    def session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        return session.as_dict() if session else None

    def record_activity(self, session_id: str, activity: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.record(session_id, activity)
        return session.as_dict() if session else None

    # --- Explorers (read-only) ---
    def citizens(self) -> Tuple[Dict[str, Any], ...]:
        return self._citizens.discover()

    def runtimes(self) -> Tuple[Dict[str, Any], ...]:
        return self._runtimes.topology()

    def providers(self) -> Tuple[Dict[str, Any], ...]:
        return self._providers.all()

    # --- Context ---
    def context(self) -> Dict[str, Any]:
        return self._context.current().as_dict()

    def set_context(self, **kwargs: str) -> Dict[str, Any]:
        return self._context.update(**kwargs).as_dict()
