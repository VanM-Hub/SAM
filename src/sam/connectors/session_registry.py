"""Session Registry — registry tambahan untuk sesi.

Sprint 116 — Connector Session.
Registry sesi dalam memori (read-friendly). Preview-only.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .session_context import SessionContext


class SessionRegistry:
    """Registry sesi connector."""

    def __init__(self) -> None:
        self._by_id: Dict[str, SessionContext] = {}
        self._by_connector: Dict[str, List[str]] = {}

    def register(self, ctx: SessionContext) -> None:
        self._by_id[ctx.session_id] = ctx
        self._by_connector.setdefault(ctx.connector_id, []).append(ctx.session_id)

    def get(self, session_id: str) -> Optional[SessionContext]:
        return self._by_id.get(session_id)

    def by_connector(self, connector_id: str) -> List[str]:
        return list(self._by_connector.get(connector_id, []))

    def count(self) -> int:
        return len(self._by_id)
