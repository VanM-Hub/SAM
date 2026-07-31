"""Dashboard Filesystem Bridge — ExecutionCard read-only (preview).

Sprint 145 — Filesystem Provider.
Menghasilkan ExecutionCard untuk provider filesystem. Read-only.
"""
from __future__ import annotations

from .filesystem_provider import FilesystemProvider
from ..dashboard.dashboard_provider import ExecutionCard


class DashboardFilesystemBridge:
    """Bridge dashboard — ExecutionCard untuk filesystem."""

    SUBSYSTEM = "filesystem"

    def __init__(self, provider: FilesystemProvider) -> None:
        self._provider = provider

    def card(self) -> ExecutionCard:
        desc = self._provider.descriptor
        return ExecutionCard(
            provider_id=desc.provider_id,
            provider_type=desc.provider_type,
            state="ready",
            summary=f"filesystem: {len(desc.implements)} contract(s)",
            detail=desc.description,
            verdict="ready",
        )

    def overview_card(self) -> ExecutionCard:
        return self.card()

    def detail_card(self) -> ExecutionCard:
        caps = self._provider.get_capabilities()
        return ExecutionCard(
            provider_id=self._provider.descriptor.provider_id,
            provider_type="filesystem",
            state="ready",
            summary=f"filesystem: {len(caps)} capability(s)",
            detail="preview-only, no disk access",
            verdict="ready",
        )
