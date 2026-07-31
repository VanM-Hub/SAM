"""Conversation Session — bridge read-only untuk sesi.

Sprint 116 — Connector Session.
Query read-only ke session manager. Tidak ada mutasi dari bridge.
"""
from __future__ import annotations
from typing import List, Optional

from .connector_session import ConnectorSessionManager
from .session_context import SessionContext
from .session_summary import SessionSummary, SessionSummarizer


class ConversationSessionBridge:
    """Bridge conversation session — read-only."""

    def __init__(self, manager: ConnectorSessionManager) -> None:
        self._manager = manager
        self._summarizer = SessionSummarizer(manager)

    def get(self, session_id: str) -> Optional[SessionContext]:
        return self._manager.get(session_id)

    def list_ids(self) -> List[str]:
        return self._manager.list_ids()

    def count(self) -> int:
        return self._manager.count()

    def summary(self) -> SessionSummary:
        return self._summarizer.summarize()
