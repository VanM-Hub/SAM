"""Conversation SQLite Bridge — query read-only (preview).

Sprint 147 — SQLite Provider.
Mengakses SQLiteProvider secara read-only.
"""
from __future__ import annotations

from .sqlite_provider import SQLiteProvider


class ConversationSQLiteBridge:
    """Bridge conversation — ringkasan read-only provider SQLite."""

    def __init__(self, provider: SQLiteProvider) -> None:
        self._provider = provider

    def describe(self) -> str:
        return f"sqlite provider v{self._provider.descriptor.version}"

    def supports(self, operation: str) -> bool:
        return self._provider.supports(operation)

    def contract(self) -> str:
        return self._provider.contract.contract_id if self._provider.contract else ""

    def preview_count(self) -> int:
        return self._provider.preview_count
