"""Cognitive Session — Sprint 29 Fase 5.

Manages cognitive sessions: each reasoning cycle is tied to a session
that tracks working memory snapshot, reflection IDs, decisions, and status.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.cognition.state import CognitiveState

logger = structlog.get_logger()


# ── Session Status Constants ──────────────────────────────────────

SESSION_ACTIVE = "ACTIVE"
SESSION_COMPLETED = "COMPLETED"
SESSION_ABANDONED = "ABANDONED"


# ── Cognitive Session Model ───────────────────────────────────────


@dataclass
class CognitiveSession:
    """A reasoning session that groups working memory, reflection, and decisions.

    Attributes:
        id: Unique session identifier.
        goal_id: Reference to a Strategic Goal, if any.
        intent_id: Reference to an active Intent, if any.
        state: CognitiveState snapshot at session start.
        working_memory_snapshot: Snapshot of working memory at session start.
        reflection_ids: List of ReflectionRecord IDs associated with this session.
        decisions: List of decision dicts made during this session.
        status: ACTIVE, COMPLETED, or ABANDONED.
        started_at: When the session began.
        ended_at: When the session ended (None if active).
    """
    id: str = ""
    goal_id: Optional[str] = None
    intent_id: Optional[str] = None
    state: Optional[Any] = None
    working_memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    reflection_ids: List[str] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    status: str = SESSION_ACTIVE
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"csess_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        state_dict = self.state.to_dict() if self.state else {}
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "intent_id": self.intent_id,
            "state": json.dumps(state_dict, default=str),
            "working_memory_snapshot": json.dumps(self.working_memory_snapshot, default=str),
            "reflection_ids": json.dumps(self.reflection_ids),
            "decisions": json.dumps(self.decisions, default=str),
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CognitiveSession:
        state_raw = data.get("state", "{}")
        if isinstance(state_raw, str):
            try:
                state_raw = json.loads(state_raw)
            except (ValueError, TypeError):
                state_raw = {}
        state = CognitiveState.from_dict(state_raw) if state_raw else None

        wm_raw = data.get("working_memory_snapshot", "{}")
        if isinstance(wm_raw, str):
            try:
                wm_raw = json.loads(wm_raw)
            except (ValueError, TypeError):
                wm_raw = {}

        refs_raw = data.get("reflection_ids", "[]")
        if isinstance(refs_raw, str):
            try:
                refs_raw = json.loads(refs_raw)
            except (ValueError, TypeError):
                refs_raw = []

        decs_raw = data.get("decisions", "[]")
        if isinstance(decs_raw, str):
            try:
                decs_raw = json.loads(decs_raw)
            except (ValueError, TypeError):
                decs_raw = []

        ended_raw = data.get("ended_at")
        ended_at = _parse_dt(ended_raw) if ended_raw else None

        return cls(
            id=data.get("id", ""),
            goal_id=data.get("goal_id"),
            intent_id=data.get("intent_id"),
            state=state,
            working_memory_snapshot=wm_raw,
            reflection_ids=refs_raw,
            decisions=decs_raw,
            status=data.get("status", SESSION_ACTIVE),
            started_at=_parse_dt(data.get("started_at")) or datetime.now(timezone.utc),
            ended_at=ended_at,
        )

    def __repr__(self) -> str:
        return (
            f"CognitiveSession(id={self.id!r}, status={self.status}, "
            f"decisions={len(self.decisions)}, reflections={len(self.reflection_ids)})"
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


# ── Cognitive Session Manager ─────────────────────────────────────


class CognitiveSessionManager:
    """Manages cognitive session lifecycle.

    Supports:
      - start_session: create a new active session
      - get_session: retrieve by ID
      - update_session: modify session fields
      - end_session: mark as COMPLETED or ABANDONED
      - get_active_session: find the currently active session
      - add_reflection: link a reflection to a session
      - add_decision: record a decision during the session
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, CognitiveSession] = {}
        self._active_session_id: Optional[str] = None
        self.logger = logger.bind(component="CognitiveSessionManager")

    async def start_session(
        self,
        goal_id: Optional[str] = None,
        intent_id: Optional[str] = None,
        state: Optional[CognitiveState] = None,
        working_memory_snapshot: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new cognitive session.

        Args:
            goal_id: Optional goal reference.
            intent_id: Optional intent reference.
            state: CognitiveState snapshot. If None, creates a default.
            working_memory_snapshot: Optional WM snapshot.

        Returns:
            The new session ID.
        """
        session = CognitiveSession(
            goal_id=goal_id,
            intent_id=intent_id,
            state=state or CognitiveState(),
            working_memory_snapshot=working_memory_snapshot or {},
        )
        self._sessions[session.id] = session
        self._active_session_id = session.id
        self.logger.info(
            "Session started",
            session_id=session.id,
            goal_id=goal_id,
            intent_id=intent_id,
        )
        return session.id

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[CognitiveSession]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> None:
        """Update fields on an existing session.

        Args:
            session_id: Target session ID.
            updates: Dict of field names to new values.
        """
        session = self._sessions.get(session_id)
        if session is None:
            self.logger.warning("Session not found for update", session_id=session_id)
            return

        # Handle special fields
        if "state" in updates:
            updates["state"] = CognitiveState.from_dict(updates["state"]) if isinstance(updates["state"], dict) else updates["state"]
        if "reflection_ids" in updates:
            if isinstance(updates["reflection_ids"], list):
                session.reflection_ids = list(set(session.reflection_ids + updates["reflection_ids"]))
            updates.pop("reflection_ids")
        if "decisions" in updates:
            if isinstance(updates["decisions"], list):
                session.decisions.extend(updates["decisions"])
            updates.pop("decisions")

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        self.logger.debug("Session updated", session_id=session_id)

    async def end_session(
        self,
        session_id: str,
        status: str = SESSION_COMPLETED,
    ) -> None:
        """End a session, marking it with the given status and timestamp."""
        session = self._sessions.get(session_id)
        if session is None:
            self.logger.warning("Session not found for end", session_id=session_id)
            return
        session.status = status
        session.ended_at = datetime.now(timezone.utc)
        if self._active_session_id == session_id:
            self._active_session_id = None
        self.logger.info(
            "Session ended",
            session_id=session_id,
            status=status,
        )

    async def get_active_session(self) -> Optional[CognitiveSession]:
        """Return the currently active session, if any."""
        if self._active_session_id is None:
            return None
        return self._sessions.get(self._active_session_id)

    async def add_reflection(
        self,
        session_id: str,
        reflection_id: str,
    ) -> None:
        """Add a reflection ID to a session's reflection list."""
        session = self._sessions.get(session_id)
        if session is None:
            self.logger.warning("Session not found for add_reflection", session_id=session_id)
            return
        if reflection_id not in session.reflection_ids:
            session.reflection_ids.append(reflection_id)
            self.logger.debug(
                "Reflection added to session",
                session_id=session_id,
                reflection_id=reflection_id,
            )

    async def add_decision(
        self,
        session_id: str,
        decision: Dict[str, Any],
    ) -> None:
        """Record a decision made during this session."""
        session = self._sessions.get(session_id)
        if session is None:
            self.logger.warning("Session not found for add_decision", session_id=session_id)
            return
        session.decisions.append(decision)
        self.logger.debug(
            "Decision added to session",
            session_id=session_id,
            decision_type=decision.get("type", "unknown"),
        )

    async def list_sessions(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[CognitiveSession]:
        """List sessions, optionally filtered by status."""
        result = list(self._sessions.values())
        if status_filter:
            result = [s for s in result if s.status == status_filter]
        result.sort(key=lambda s: s.started_at, reverse=True)
        return result[:limit]

    async def clear(self) -> None:
        """Clear all sessions (for testing)."""
        self._sessions.clear()
        self._active_session_id = None
