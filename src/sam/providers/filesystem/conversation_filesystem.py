"""Conversation Filesystem Bridge — query read-only (preview).

Sprint 145 — Filesystem Provider.
Mengakses FilesystemProvider secara read-only.
"""
from __future__ import annotations
from typing import List

from .filesystem_provider import FilesystemProvider, FILESYSTEM_OPERATIONS


class ConversationFilesystemBridge:
    """Bridge conversation — ringkasan read-only provider filesystem."""

    def __init__(self, provider: FilesystemProvider) -> None:
        self._provider = provider

    def describe(self) -> str:
        return f"filesystem provider v{self._provider.descriptor.version}"

    def operations(self) -> List[str]:
        return list(FILESYSTEM_OPERATIONS)

    def supports(self, operation: str) -> bool:
        return self._provider.supports(operation)

    def preview_count(self) -> int:
        return self._provider.preview_count
