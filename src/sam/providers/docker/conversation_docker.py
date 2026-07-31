"""Conversation Docker Bridge — query read-only (preview).

Sprint 148 — Docker Provider.
Mengakses DockerProvider secara read-only.
"""
from __future__ import annotations

from .docker_provider import DockerProvider


class ConversationDockerBridge:
    """Bridge conversation — ringkasan read-only provider docker."""

    def __init__(self, provider: DockerProvider) -> None:
        self._provider = provider

    def describe(self) -> str:
        return f"docker provider v{self._provider.descriptor.version}"

    def supports(self, operation: str) -> bool:
        return self._provider.supports(operation)

    def contract(self) -> str:
        return self._provider.contract.contract_id if self._provider.contract else ""

    def preview_count(self) -> int:
        return self._provider.preview_count
