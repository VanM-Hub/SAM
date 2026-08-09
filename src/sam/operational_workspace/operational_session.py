"""Operational Session - WP-02 (MISSION-4.6 / IP-4.6-001).

Mengelola sesi operasional pengguna. Seluruh aktivitas dalam satu Session,
Session mempertahankan context, dapat dipulihkan, dapat diaudit.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple



def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class OperationalSessionState:
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

    _VALID = (ACTIVE, PAUSED, COMPLETED)

    @classmethod
    def valid(cls, state: str) -> bool:
        return state in cls._VALID


@dataclass(frozen=True)
class SessionContext:
    """Konteks sesi."""

    user: str = ""
    workspace_id: str = ""
    started_at: str = field(default_factory=_now_utc)
    environment: str = ""

    def as_dict(self) -> dict:
        return {
            "user": self.user,
            "workspace_id": self.workspace_id,
            "started_at": self.started_at,
            "environment": self.environment,
        }


@dataclass(frozen=True)
class SessionHistoryEntry:
    """Satu catatan riwayat sesi."""

    activity: str
    detail: str = ""
    at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "activity": self.activity,
            "detail": self.detail,
            "at": self.at,
        }


@dataclass(frozen=True)
class OperationalSession:
    """Sesi operasional (auditable, recoverable)."""

    session_id: str
    context: SessionContext
    state: str = OperationalSessionState.ACTIVE
    history: Tuple[SessionHistoryEntry, ...] = field(default_factory=tuple)

    def record(self, activity: str, detail: str = "") -> "OperationalSession":
        return OperationalSession(
            session_id=self.session_id,
            context=self.context,
            state=self.state,
            history=self.history
            + (SessionHistoryEntry(activity=activity, detail=detail),),
        )

    def complete(self) -> "OperationalSession":
        return OperationalSession(
            session_id=self.session_id,
            context=self.context,
            state=OperationalSessionState.COMPLETED,
            history=self.history,
        )

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "context": self.context.as_dict(),
            "state": self.state,
            "history": [h.as_dict() for h in self.history],
        }


class SessionManager:
    """Manajer sesi (create, get, recover)."""

    def __init__(self) -> None:
        self._sessions: Dict[str, OperationalSession] = {}

    def create(self, *, user: str = "", workspace_id: str = "") -> OperationalSession:
        session = OperationalSession(
            session_id=uuid.uuid4().hex,
            context=SessionContext(user=user, workspace_id=workspace_id),
        ).record("started", "session created")
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[OperationalSession]:
        return self._sessions.get(session_id)

    def record(
        self, session_id: str, activity: str, detail: str = ""
    ) -> Optional[OperationalSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        updated = session.record(activity, detail)
        self._sessions[session_id] = updated
        return updated

    def complete(self, session_id: str) -> Optional[OperationalSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        updated = session.complete()
        self._sessions[session_id] = updated
        return updated

    def recover(self, session_id: str, snapshot: Dict[str, Any]) -> Optional[OperationalSession]:
        session = self._sessions.get(session_id)
        if session is not None:
            return session
        # recovery dari snapshot (belum di-construct ulang -> log draft)
        new_session = OperationalSession(
            session_id=session_id,
            context=SessionContext(
                user=snapshot.get("user", ""),
                workspace_id=snapshot.get("workspace_id", ""),
            ),
        )
        self._sessions[session_id] = new_session
        return new_session

    def all(self) -> Tuple[OperationalSession, ...]:
        return tuple(self._sessions.values())

    def audit(self) -> Dict[str, Any]:
        return {
            "session_count": len(self._sessions),
            "sessions": [s.as_dict() for s in self._sessions.values()],
        }
