"""Dashboard Docker Bridge — ExecutionCard read-only (preview).

Sprint 148 — Docker Provider.
Menghasilkan ExecutionCard untuk provider docker. Read-only.
"""
from __future__ import annotations

from .docker_provider import DockerProvider
from ..dashboard.dashboard_provider import ExecutionCard


class DashboardDockerBridge:
    """Bridge dashboard — ExecutionCard untuk docker."""

    SUBSYSTEM = "docker"

    def __init__(self, provider: DockerProvider) -> None:
        self._provider = provider

    def card(self) -> ExecutionCard:
        desc = self._provider.descriptor
        n_caps = len(self._provider.capabilities)
        return ExecutionCard(
            provider_id=desc.provider_id,
            provider_type=desc.provider_type,
            state="ready",
            summary=f"docker: {n_caps} capability(s) (container/image/compose)",
            detail=desc.description,
            verdict="ready",
        )

    def verdict_card(self) -> ExecutionCard:
        return self.card()
