"""Transition Monitor — monitor transisi mission (Sprint 161).

Agent Runtime — memantau lifecycle mission. Read-only, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..state.state_machine import StateMachine
from ..state.transition_history import TransitionHistory
from ..coordinator.runtime_queue import RuntimeQueue


@dataclass(frozen=True)
class TransitionStatus:
    """Status transisi (immutable)."""
    mission_id: str
    state: str = "Created"
    current_runtime: Optional[str] = None
    progress_percent: int = 0
    waiting_reason: str = ""
    completed_steps: int = 0
    remaining_steps: int = 0


class TransitionMonitor:
    """Monitor transisi. Read-only, deterministik."""

    def __init__(
        self,
        machine: StateMachine,
        history: TransitionHistory,
        queue: RuntimeQueue,
        pipeline_length: int,
    ) -> None:
        self._machine = machine
        self._history = history
        self._queue = queue
        self._pipeline_length = max(1, pipeline_length)

    def status(self, mission_id: str) -> TransitionStatus:
        state = self._machine.current(mission_id)
        current_state = state.state if state else "Created"
        completed = self._history.applied_count()
        remaining = max(0, self._pipeline_length - completed)
        progress = min(100, int((completed / self._pipeline_length) * 100))
        nxt = self._queue.next_pending()
        current_runtime = nxt.runtime_name if nxt else None
        waiting_reason = ""
        if current_state == "Waiting":
            waiting_reason = "mission waiting for signal (no auto retry)"
        return TransitionStatus(
            mission_id=mission_id,
            state=current_state,
            current_runtime=current_runtime,
            progress_percent=progress,
            waiting_reason=waiting_reason,
            completed_steps=completed,
            remaining_steps=remaining,
        )


__all__ = ["TransitionMonitor", "TransitionStatus"]
