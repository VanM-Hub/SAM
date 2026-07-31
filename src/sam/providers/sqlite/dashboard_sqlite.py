"""Dashboard SQLite Bridge — ExecutionCard read-only (preview).

Sprint 147 — SQLite Provider.
Menghasilkan ExecutionCard untuk provider SQLite. Read-only.
"""
from __future__ import annotations

from .sqlite_provider import SQLiteProvider
from ..dashboard.dashboard_provider import ExecutionCard


class DashboardSQLiteBridge:
    """Bridge dashboard — ExecutionCard untuk SQLite."""

    SUBSYSTEM = "sqlite"

    def __init__(self, provider: SQLiteProvider) -> None:
        self._provider = provider

    def card(self) -> ExecutionCard:
        desc = self._provider.descriptor
        return ExecutionCard(
            provider_id=desc.provider_id,
            provider_type=desc.provider_type,
            state="ready",
            summary="sqlite: build & preview query",
            detail=desc.description,
            verdict="ready",
        )

    def verdict_card(self) -> ExecutionCard:
        return self.card()
