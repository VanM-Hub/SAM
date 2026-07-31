"""Conversation Session Bridge — query read-only (Sprint 157)."""
from __future__ import annotations
from typing import List

from .mission_registry import MissionRegistry


class ConversationSessionBridge:
    """Bridge conversation — ringkasan sesi mission read-only."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def show_current_state(self, mission_id: str) -> str:
        st = self._registry.get_state(mission_id)
        return st.state if st else "unknown"

    def show_summary(self) -> dict:
        s = self._registry.session_summary()
        return {"total": s.total, "open": s.open, "active": s.active}

    def count(self) -> int:
        return self._registry.session_summary().total
