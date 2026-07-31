"""Conversation Coordinator Bridge — query read-only (Sprint 160)."""
from __future__ import annotations
from typing import List, Optional

from .runtime_registry import RuntimeRegistry
from .runtime_queue import RuntimeQueue


class ConversationCoordinatorBridge:
    """Bridge conversation — ringkasan coordinator read-only."""

    def __init__(self, registry: RuntimeRegistry, queue: RuntimeQueue = None) -> None:
        self._registry = registry
        self._queue = queue if queue is not None else RuntimeQueue()

    def show_current_runtime(self) -> Optional[str]:
        nxt = self._queue.next_pending()
        return nxt.runtime_name if nxt else None

    def show_registry(self) -> List[str]:
        return self._registry.names()

    def show_pending(self) -> int:
        return len(self._queue.pending())
