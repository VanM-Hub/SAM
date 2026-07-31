"""Dashboard Shell Bridge — ExecutionCard read-only (preview).

Sprint 146 — Shell Provider.
Menghasilkan ExecutionCard untuk provider shell. Read-only.
"""
from __future__ import annotations

from .shell_provider import ShellProvider
from ..dashboard.dashboard_provider import ExecutionCard


class DashboardShellBridge:
    """Bridge dashboard — ExecutionCard untuk shell."""

    SUBSYSTEM = "shell"

    def __init__(self, provider: ShellProvider) -> None:
        self._provider = provider

    def card(self) -> ExecutionCard:
        desc = self._provider.descriptor
        return ExecutionCard(
            provider_id=desc.provider_id,
            provider_type=desc.provider_type,
            state="ready",
            summary="shell: build & preview command",
            detail=desc.description,
            verdict="ready",
        )

    def verdict_card(self) -> ExecutionCard:
        return self.card()
