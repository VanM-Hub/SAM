"""Dashboard OpenClaw Bridge — ExecutionCard read-only (preview).

Sprint 149 — OpenClaw Provider.
Menghasilkan ExecutionCard untuk provider openclaw. Read-only.
"""
from __future__ import annotations

from .openclaw_provider import OpenClawProvider
from ..dashboard.dashboard_provider import ExecutionCard


class DashboardOpenClawBridge:
    """Bridge dashboard — ExecutionCard untuk openclaw."""

    SUBSYSTEM = "openclaw"

    def __init__(self, provider: OpenClawProvider) -> None:
        self._provider = provider

    def card(self) -> ExecutionCard:
        desc = self._provider.descriptor
        return ExecutionCard(
            provider_id=desc.provider_id,
            provider_type=desc.provider_type,
            state="ready",
            summary="openclaw: build & preview tool",
            detail=desc.description,
            verdict="ready",
        )

    def verdict_card(self) -> ExecutionCard:
        return self.card()
