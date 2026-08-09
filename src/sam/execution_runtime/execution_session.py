"""Execution Session - IP-4.1-001 WP-03.

Provider Execution Foundation.
Membangun session operasional untuk seluruh aktivitas execution.

Scope (Foundation immutable):
- Setiap execution memiliki Session.
- Session immutable setelah selesai (Article VI).
- Session dapat diaudit (Article XI).
- Session Metadata & Context tersedia.
- Deterministik (Article VII): sessid deterministik dari input.

Tidak ada network, tidak ada authority baru. Hanya pengelolaan lifecycle session.
"""

from __future__ import annotations

import enum
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple


class SessionState(str, enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


# Urutan lifecycle yang valid (deterministik).
_VALID_TRANSITIONS = {
    SessionState.CREATED: {SessionState.ACTIVE, SessionState.CANCELLED, SessionState.FAILED},
    SessionState.ACTIVE: {SessionState.COMPLETED, SessionState.FAILED, SessionState.CANCELLED},
    SessionState.COMPLETED: {SessionState.CLOSED},
    SessionState.FAILED: {SessionState.CLOSED},
    SessionState.CANCELLED: {SessionState.CLOSED},
    SessionState.CLOSED: set(),
}


@dataclass(frozen=True)
class SessionMetadata:
    """Metadata session (immutable)."""

    created_at: str
    source: str = ""            # api | cli | web | internal
    tags: Tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    def as_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "source": self.source,
            "tags": list(self.tags),
            "description": self.description,
        }


@dataclass(frozen=True)
class SessionContext:
    """Konteks session (immutable) - menelusuri ke request/descriptor."""

    execution_ids: Tuple[str, ...] = field(default_factory=tuple)
    provider_id: str = ""
    operation: str = ""

    def as_dict(self) -> dict:
        return {
            "execution_ids": list(self.execution_ids),
            "provider_id": self.provider_id,
            "operation": self.operation,
        }


@dataclass(frozen=True)
class SessionEvent:
    """Satu event lifecycle session (immutable, Article XI)."""

    state: str
    occurred_at: str
    actor: str = "execution"

    def as_dict(self) -> dict:
        return {"state": self.state, "occurred_at": self.occurred_at, "actor": self.actor}


@dataclass(frozen=True)
class ExecutionSession:
    """Session eksekusi (immutable setelah selesai)."""

    session_id: str
    state: SessionState
    metadata: SessionMetadata
    context: SessionContext
    events: Tuple[SessionEvent, ...] = field(default_factory=tuple)
    finalized: bool = False

    def is_final(self) -> bool:
        return self.state in (SessionState.COMPLETED, SessionState.FAILED,
                              SessionState.CANCELLED, SessionState.CLOSED)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "metadata": self.metadata.as_dict(),
            "context": self.context.as_dict(),
            "events": [e.as_dict() for e in self.events],
            "finalized": self.finalized,
        }


# ---------------------------------------------------------------------------
# Session factory (deterministik)
# ---------------------------------------------------------------------------


def deterministic_session_id(provider_id: str, execution_id: str) -> str:
    """Session id deterministik dari input (Article VII).

    Tidak menggunakan RNG bila execution_id tersedia; fallback uuid untuk
    session tanpa execution context.
    """
    if execution_id:
        digest = hashlib.sha256("{}:{}".format(provider_id, execution_id).encode("utf-8")).hexdigest()[:12]
        return "sess-{}-{}".format(provider_id, digest)
    return "sess-{}".format(uuid.uuid4().hex[:12])


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------


class ExecutionSessionManager:
    """Manager lifecycle session eksekusi (read-only + state terbatas).

    Session bersifat append-only: setelah finalized, tidak dapat berubah.
    Deterministik untuk pembuatan id; lifecycle dijaga lewat whitelist transisi.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, ExecutionSession] = {}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create(self, provider_id: str, execution_id: str = "",
               source: str = "internal", tags: Tuple[str, ...] = (),
               description: str = "", operation: str = "") -> ExecutionSession:
        """Buat session baru (CREATED). Dapat diaudit via events."""
        session_id = deterministic_session_id(provider_id, execution_id)
        if session_id in self._sessions:
            return self._sessions[session_id]  # idempotent: session yang sama
        now = self._now()
        session = ExecutionSession(
            session_id=session_id,
            state=SessionState.CREATED,
            metadata=SessionMetadata(created_at=now, source=source, tags=tags, description=description),
            context=SessionContext(
                execution_ids=(execution_id,) if execution_id else (),
                provider_id=provider_id, operation=operation,
            ),
            events=(SessionEvent(SessionState.CREATED.value, now),),
            finalized=False,
        )
        self._sessions[session_id] = session
        return session

    def transition(self, session_id: str, new_state: SessionState,
                   actor: str = "execution") -> Optional[ExecutionSession]:
        """Transisi lifecycle session. Immutable setelah finalized.

        Mengembalikan None bila transisi tidak valid / session tidak ada.
        """
        current = self._sessions.get(session_id)
        if current is None:
            return None
        if current.finalized:
            return None  # sudah final; tidak ada transisi lebih lanjut (immutable)
        allowed = _VALID_TRANSITIONS.get(current.state, set())
        if new_state not in allowed:
            return None
        events = current.events + (SessionEvent(new_state.value, self._now(), actor),)
        # Final hanya saat CLOSED (COMPLETED/FAILED/CANCELLED masih boleh -> CLOSED)
        finalized = (new_state == SessionState.CLOSED)
        updated = ExecutionSession(
            session_id=current.session_id,
            state=new_state,
            metadata=current.metadata,
            context=current.context,
            events=events,
            finalized=finalized,
        )
        self._sessions[session_id] = updated
        return updated

    def get(self, session_id: str) -> Optional[ExecutionSession]:
        return self._sessions.get(session_id)

    def all(self) -> Tuple[ExecutionSession, ...]:
        return tuple(self._sessions.values())

    def by_provider(self, provider_id: str) -> Tuple[ExecutionSession, ...]:
        return tuple(s for s in self._sessions.values() if s.context.provider_id == provider_id)

    def count(self) -> int:
        return len(self._sessions)

    def clear(self) -> None:
        self._sessions.clear()
