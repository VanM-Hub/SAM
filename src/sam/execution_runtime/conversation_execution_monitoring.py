"""Conversation Execution Monitoring (Sprint 256).

Program C - Real Execution Runtime.
Read-only bridge: status monitoring pada konteks percakapan.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_monitor import ExecutionMonitor


@dataclass(frozen=True)
class ConversationExecutionMonitoringView:
    """View monitoring pada percakapan (immutable)."""
    conversation_id: str
    recorded: int = 0
    healthy: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"conversation_id": self.conversation_id, "recorded": self.recorded,
                "healthy": self.healthy, "external_calls": self.external_calls}


class ConversationExecutionMonitoring:
    """Bridge monitoring <-> conversation. Read-only."""

    def __init__(self, monitor: ExecutionMonitor | None = None) -> None:
        self._monitor = monitor or ExecutionMonitor()

    def view(self, conversation_id: str) -> ConversationExecutionMonitoringView:
        return ConversationExecutionMonitoringView(
            conversation_id=conversation_id,
            recorded=self._monitor.history.count(),
            healthy=self._monitor.health().ok,
            external_calls=0,
        )
