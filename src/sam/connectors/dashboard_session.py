"""Dashboard Session — bridge read-only untuk UI sesi.

Sprint 116 — Connector Session.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_session import ConnectorSessionManager
from .session_summary import SessionSummarizer
from .dashboard_connector import ExecutionCard


class DashboardSessionBridge:
    """Bridge dashboard session — 5 ExecutionCard."""

    def __init__(self, manager: ConnectorSessionManager) -> None:
        self._manager = manager
        self._summarizer = SessionSummarizer(manager)

    def engine_card(self) -> ExecutionCard:
        s = self._summarizer.summarize()
        return ExecutionCard(card_id="session.engine", title="Session Engine",
                             summary=f"{s.total_sessions} sessions",
                             detail=f"active {s.active}", verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="session.subsystem", title="Session Subsystem",
                             summary="In-memory sessions", detail="preview-only",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        s = self._summarizer.summarize()
        return ExecutionCard(card_id="session.summary", title="Session Summary",
                             summary=f"{s.active} active / {s.closed} closed",
                             detail="session lifecycle", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        ids = self._manager.list_ids()
        return ExecutionCard(card_id="session.detail", title="Session Detail",
                             summary=", ".join(ids) if ids else "(none)",
                             detail="active sessions", verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="session.verdict", title="Session Verdict",
                             summary="Sessions ready", detail="Ready for routing",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
