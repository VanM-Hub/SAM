"""Conversation Execution Foundation (Sprint 250).

Program C - Real Execution Runtime.
Read-only bridge: mendeskripsikan kapabilitas execution pada konteks percakapan.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_registry import ExecutionRegistry
from .execution_descriptor import ExecutionDescriptor


@dataclass(frozen=True)
class ConversationExecutionFoundationView:
    """View foundation pada konteks percakapan (immutable)."""
    conversation_id: str
    available: int = 0
    execute_available: int = 0
    rollback_available: int = 0
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "available": self.available,
            "execute_available": self.execute_available,
            "rollback_available": self.rollback_available,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationExecutionFoundation:
    """Bridge execution foundation <-> conversation. Read-only."""

    def __init__(self, registry: ExecutionRegistry | None = None) -> None:
        self._registry = registry or ExecutionRegistry()

    def view(self, conversation_id: str) -> ConversationExecutionFoundationView:
        return ConversationExecutionFoundationView(
            conversation_id=conversation_id,
            available=self._registry.count(),
            execute_available=len(self._registry.by_mode("execute")),
            rollback_available=len(self._registry.by_mode("rollback")),
            preview_only=True,
            external_calls=0,
        )
