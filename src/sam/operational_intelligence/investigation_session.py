"""Investigation Session - WP-02 (MISSION-4.2 / IP-4.2-001).

Mengelola seluruh aktivitas investigasi dalam satu sesi operasional.

Seluruh investigasi memiliki Session; Session mempertahankan context,
dapat diaudit, dan immutable setelah selesai.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple



def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class SessionState:
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

    _ORDER = (ACTIVE, PAUSED, COMPLETED, FAILED)

    @classmethod
    def valid(cls, state: str) -> bool:
        return state in cls._ORDER


@dataclass(frozen=True)
class SessionContext:
    """Konteks sesi (mempertahankan konteks investigasi)."""

    investigation_id: str
    operator: str = ""
    target_ids: Tuple[str, ...] = field(default_factory=tuple)
    start_reason: str = ""
    environment: str = ""

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "operator": self.operator,
            "target_ids": list(self.target_ids),
            "start_reason": self.start_reason,
            "environment": self.environment,
        }


@dataclass(frozen=True)
class SessionHistoryEntry:
    """Satu catatan riwayat sesi (immutable)."""

    session_id: str
    timestamp: str
    event: str  # created | scope_set | evidence_added | completed | failed
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "event": self.event,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class SessionStateSnapshot:
    """State sesi saat ini (immutable)."""

    session_id: str
    state: str
    investigation_ids: Tuple[str, ...] = field(default_factory=tuple)
    history: Tuple[SessionHistoryEntry, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "investigation_ids": list(self.investigation_ids),
            "history": [h.as_dict() for h in self.history],
        }


@dataclass(frozen=True)
class InvestigationSession:
    """Sesi investigasi operasional (auditable)."""

    session_id: str
    created_at: str
    context: SessionContext
    state: str = SessionState.ACTIVE
    investigations: Tuple[str, ...] = field(default_factory=tuple)
    history: Tuple[SessionHistoryEntry, ...] = field(default_factory=tuple)
    session_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        context: SessionContext,
        session_id: Optional[str] = None,
    ) -> "InvestigationSession":
        return cls(
            session_id=session_id or uuid.uuid4().hex,
            created_at=_now_utc(),
            context=context,
            state=SessionState.ACTIVE,
            history=(
                SessionHistoryEntry(
                    session_id=session_id or "",
                    timestamp=_now_utc(),
                    event="created",
                ),
            ),
        )

    def add_investigation(self, investigation_id: str) -> "InvestigationSession":
        if self.state != SessionState.ACTIVE:
            raise ValueError("Session is not active")
        if investigation_id in self.investigations:
            return self
        return InvestigationSession(
            session_id=self.session_id,
            created_at=self.created_at,
            context=self.context,
            state=SessionState.ACTIVE,
            investigations=self.investigations + (investigation_id,),
            history=self.history
            + (
                SessionHistoryEntry(
                    session_id=self.session_id,
                    timestamp=_now_utc(),
                    event="investigation_added",
                    detail=investigation_id,
                ),
            ),
        )

    def complete(self) -> "InvestigationSession":
        if self.state == SessionState.COMPLETED:
            return self
        return InvestigationSession(
            session_id=self.session_id,
            created_at=self.created_at,
            context=self.context,
            state=SessionState.COMPLETED,
            investigations=self.investigations,
            history=self.history
            + (
                SessionHistoryEntry(
                    session_id=self.session_id,
                    timestamp=_now_utc(),
                    event="completed",
                ),
            ),
        )

    def fail(self, detail: str = "") -> "InvestigationSession":
        if self.state in (SessionState.COMPLETED, SessionState.FAILED):
            return self
        return InvestigationSession(
            session_id=self.session_id,
            created_at=self.created_at,
            context=self.context,
            state=SessionState.FAILED,
            investigations=self.investigations,
            history=self.history
            + (
                SessionHistoryEntry(
                    session_id=self.session_id,
                    timestamp=_now_utc(),
                    event="failed",
                    detail=detail,
                ),
            ),
        )

    @property
    def is_complete(self) -> bool:
        return self.state == SessionState.COMPLETED

    @property
    def is_immutable(self) -> bool:
        return self.state in (SessionState.COMPLETED, SessionState.FAILED)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "context": self.context.as_dict(),
            "state": self.state,
            "investigations": list(self.investigations),
            "history": [h.as_dict() for h in self.history],
            "session_hash": self._compute_hash(),
        }

    def _compute_hash(self) -> str:
        import hashlib

        h = hashlib.sha256()
        for part in (
            self.session_id,
            self.created_at,
            self.state,
            *self.investigations,
            *[f"{e.event}:{e.detail}" for e in self.history],
        ):
            h.update(str(part).strip().lower().encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()


class InvestigationSessionManager:
    """Registry sesi investigasi (append-only, read-only setelah immutable)."""

    def __init__(self) -> None:
        self._sessions: Dict[str, InvestigationSession] = {}

    def create_session(
        self, context: SessionContext
    ) -> InvestigationSession:
        session = InvestigationSession.create(context=context)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[InvestigationSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> Tuple[InvestigationSession, ...]:
        return tuple(self._sessions.values())

    def snapshot(self, session_id: str) -> Optional[SessionStateSnapshot]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        return SessionStateSnapshot(
            session_id=session.session_id,
            state=session.state,
            investigation_ids=session.investigations,
            history=session.history,
        )
