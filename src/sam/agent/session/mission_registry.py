"""Mission Registry — registry mission session (Sprint 157).

Agent Runtime — registry append + read-only query. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .mission_session import MissionSession
from .mission_state import MissionState
from .mission_context import MissionContext
from .mission_snapshot import MissionSnapshot


@dataclass(frozen=True)
class SessionSummary:
    """Ringkasan sesi (immutable)."""
    total: int = 0
    open: int = 0
    active: int = 0
    total_external_calls: int = 0


class MissionRegistry:
    """Registry mission. Append + query read-only."""

    def __init__(self) -> None:
        self._sessions: List[MissionSession] = []
        self._states: Dict[str, MissionState] = {}
        self._contexts: Dict[str, MissionContext] = {}
        self._snapshots: List[MissionSnapshot] = []

    # --- sesi ---
    def open_session(self, session: MissionSession) -> bool:
        self._sessions.append(session)
        return True

    def get_session(self, session_id: str) -> Optional[MissionSession]:
        for s in self._sessions:
            if s.session_id == session_id:
                return s
        return None

    def sessions_for_mission(self, mission_id: str) -> List[MissionSession]:
        return [s for s in self._sessions if s.mission_id == mission_id]

    def session_summary(self) -> SessionSummary:
        return SessionSummary(
            total=len(self._sessions),
            open=sum(1 for s in self._sessions if s.open),
            active=sum(1 for s in self._sessions if s.active),
            total_external_calls=sum(s.external_calls for s in self._sessions),
        )

    # --- state ---
    def set_state(self, state: MissionState) -> bool:
        self._states[state.mission_id] = state
        return True

    def get_state(self, mission_id: str) -> Optional[MissionState]:
        return self._states.get(mission_id)

    # --- konteks ---
    def set_context(self, context: MissionContext) -> bool:
        self._contexts[context.mission_id] = context
        return True

    def get_context(self, mission_id: str) -> Optional[MissionContext]:
        return self._contexts.get(mission_id)

    # --- snapshot ---
    def record_snapshot(self, snapshot: MissionSnapshot) -> bool:
        self._snapshots.append(snapshot)
        return True

    def snapshots(self, mission_id: str) -> List[MissionSnapshot]:
        return [s for s in self._snapshots if s.mission_id == mission_id]

    def count_missions(self) -> int:
        return len(self._states)


__all__ = [
    "MissionRegistry", "SessionSummary",
    "MissionSession", "MissionState", "MissionContext", "MissionSnapshot",
]
