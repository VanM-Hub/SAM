"""Connector Session — engine sesi connector.

Sprint 116 — Connector Session.
Kelola siklus hidup sesi (create/activate/close). In-memory, sinkronus.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .session_context import SessionContext


class ConnectorSessionManager:
    """Manajemen sesi connector (preview-only, in-memory)."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionContext] = {}

    def create(self, session_id: str, connector_id: str, binding_id: str = "") -> SessionContext:
        ctx = SessionContext(session_id, connector_id, binding_id, "created")
        self._sessions[session_id] = ctx
        return ctx

    def activate(self, session_id: str) -> Optional[SessionContext]:
        ctx = self._sessions.get(session_id)
        if ctx is None:
            return None
        new_ctx = SessionContext(ctx.session_id, ctx.connector_id, ctx.binding_id,
                                 "active", ctx.variables)
        self._sessions[session_id] = new_ctx
        return new_ctx

    def close(self, session_id: str) -> Optional[SessionContext]:
        ctx = self._sessions.get(session_id)
        if ctx is None:
            return None
        new_ctx = SessionContext(ctx.session_id, ctx.connector_id, ctx.binding_id,
                                 "closed", ctx.variables)
        self._sessions[session_id] = new_ctx
        return new_ctx

    def get(self, session_id: str) -> Optional[SessionContext]:
        return self._sessions.get(session_id)

    def list_ids(self) -> List[str]:
        return list(self._sessions.keys())

    def count(self) -> int:
        return len(self._sessions)
