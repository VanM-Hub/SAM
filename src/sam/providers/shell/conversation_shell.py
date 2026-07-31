"""Conversation Shell Bridge — query read-only (preview).

Sprint 146 — Shell Provider.
Mengakses ShellProvider secara read-only.
"""
from __future__ import annotations

from .shell_provider import ShellProvider


class ConversationShellBridge:
    """Bridge conversation — ringkasan read-only provider shell."""

    def __init__(self, provider: ShellProvider) -> None:
        self._provider = provider

    def describe(self) -> str:
        return f"shell provider v{self._provider.descriptor.version}"

    def supports(self, operation: str) -> bool:
        return self._provider.supports(operation)

    def preview_count(self) -> int:
        return self._provider.preview_count

    def contract(self) -> str:
        return self._provider.contract.contract_id if self._provider.contract else ""
