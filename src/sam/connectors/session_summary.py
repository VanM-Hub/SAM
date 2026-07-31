"""Session Summary — engine ringkasan sesi.

Sprint 116 — Connector Session.
Ringkasan agregat sesi (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_session import ConnectorSessionManager


@dataclass(frozen=True)
class SessionSummary:
    """Ringkasan agregat sesi."""
    total_sessions: int = 0
    active: int = 0
    closed: int = 0
    created: int = 0


class SessionSummarizer:
    """Bangun ringkasan sesi."""

    def __init__(self, manager: ConnectorSessionManager) -> None:
        self._manager = manager

    def summarize(self) -> SessionSummary:
        active = closed = created = 0
        for sid in self._manager.list_ids():
            ctx = self._manager.get(sid)
            if ctx:
                if ctx.state == "active":
                    active += 1
                elif ctx.state == "closed":
                    closed += 1
                else:
                    created += 1
        return SessionSummary(self._manager.count(), active, closed, created)
