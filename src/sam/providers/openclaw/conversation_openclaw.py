"""Conversation OpenClaw Bridge — query read-only (preview).

Sprint 149 — OpenClaw Provider.
Mengakses OpenClawProvider secara read-only.
"""
from __future__ import annotations

from .openclaw_provider import OpenClawProvider


class ConversationOpenClawBridge:
    """Bridge conversation — ringkasan read-only provider openclaw."""

    def __init__(self, provider: OpenClawProvider) -> None:
        self._provider = provider

    def describe(self) -> str:
        return f"openclaw provider v{self._provider.descriptor.version}"

    def supports(self, operation: str) -> bool:
        return self._provider.supports(operation)

    def contract(self) -> str:
        return self._provider.contract.contract_id if self._provider.contract else ""

    def preview_count(self) -> int:
        return self._provider.preview_count
