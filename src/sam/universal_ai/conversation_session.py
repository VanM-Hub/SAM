"""Conversation Session - WP-22 (MISSION-5.1 / IP-5.1-003).

Lifecycle session conversation. Session state bukan governance authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionState(str, Enum):
    """State lifecycle sebuah session."""

    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ConversationSession:
    """Sebuah session dalam sebuah conversation."""

    session_id: str
    conversation_id: str
    state: SessionState = SessionState.CREATED
    provider_id: str = ""
    model_id: str = ""
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "created_at": self.created_at,
        }


class SessionManager:
    """Mengelola lifecycle session."""

    def __init__(self) -> None:
        self._sessions = {}

    def create(self, conversation_id: str, provider_id: str = "", model_id: str = "") -> ConversationSession:
        session = ConversationSession(
            session_id=_gen(),
            conversation_id=conversation_id,
            provider_id=provider_id,
            model_id=model_id,
            state=SessionState.ACTIVE,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str):
        return self._sessions.get(session_id)

    def resume(self, session_id: str):
        session = self._sessions.get(session_id)
        if session is None or session.state in (SessionState.COMPLETED, SessionState.EXPIRED):
            return None
        updated = ConversationSession(
            session_id=session.session_id,
            conversation_id=session.conversation_id,
            state=SessionState.ACTIVE,
            provider_id=session.provider_id,
            model_id=session.model_id,
            created_at=session.created_at,
        )
        self._sessions[session_id] = updated
        return updated

    def pause(self, session_id: str):
        session = self._sessions.get(session_id)
        if session is None:
            return None
        updated = ConversationSession(
            session_id=session.session_id,
            conversation_id=session.conversation_id,
            state=SessionState.PAUSED,
            provider_id=session.provider_id,
            model_id=session.model_id,
            created_at=session.created_at,
        )
        self._sessions[session_id] = updated
        return updated

    def complete(self, session_id: str):
        return _set_state(self._sessions, session_id, SessionState.COMPLETED)

    def expire(self, session_id: str):
        return _set_state(self._sessions, session_id, SessionState.EXPIRED)

    def list_active(self):
        return tuple(s for s in self._sessions.values() if s.state == SessionState.ACTIVE)


def _gen() -> str:
    import uuid

    return uuid.uuid4().hex


def _set_state(store, session_id: str, state: SessionState):
    session = store.get(session_id)
    if session is None:
        return None
    updated = ConversationSession(
        session_id=session.session_id,
        conversation_id=session.conversation_id,
        state=state,
        provider_id=session.provider_id,
        model_id=session.model_id,
        created_at=session.created_at,
    )
    store[session_id] = updated
    return updated
