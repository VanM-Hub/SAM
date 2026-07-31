"""Conversation State Bridge — query read-only (Sprint 158)."""
from __future__ import annotations
from typing import List

from .state_machine import StateMachine
from .transition_history import TransitionHistory


class ConversationStateBridge:
    """Bridge conversation — state lifecycle read-only."""

    def __init__(self, machine: StateMachine, history: TransitionHistory = None) -> None:
        self._machine = machine
        self._history = history

    def show_current_state(self, mission_id: str) -> str:
        st = self._machine.current(mission_id)
        return st.state if st else "unknown"

    def show_transition_history(self, mission_id: str) -> List[str]:
        if not self._history:
            return []
        return [
            f"{e.from_state}->{e.to_state}" for e in self._history.events(mission_id)
        ]

    def status(self) -> str:
        return "state machine ready"
