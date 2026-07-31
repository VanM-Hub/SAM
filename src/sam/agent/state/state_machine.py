"""State Machine — mesin state lifecycle agent (Sprint 158).

Agent Runtime — state machine deterministic. Tidak ada auto retry.
Urutan:
Created -> Preparing -> Running -> (Waiting <-> Running) -> Completed
Created -> Cancelled (dari mana saja sebelum terminal)
Setiap state -> Failed (dari non-terminal)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from .agent_state import (
    CREATED, PREPARING, RUNNING, WAITING, COMPLETED, CANCELLED, FAILED,
    TERMINAL_STATES, ALL_STATES, AgentState,
)


@dataclass(frozen=True)
class TransitionResult:
    """Hasil transisi state (immutable)."""
    mission_id: str
    allowed: bool
    from_state: str = ""
    to_state: str = ""
    reason: str = ""

    @property
    def applied(self) -> bool:
        return self.allowed


class StateMachine:
    """State machine lifecycle mission. Deterministik, no auto retry."""

    # transisi yang diizinkan
    ALLOWED: Dict[str, Set[str]] = {
        CREATED: {PREPARING, CANCELLED, FAILED},
        PREPARING: {RUNNING, CANCELLED, FAILED},
        RUNNING: {WAITING, COMPLETED, CANCELLED, FAILED},
        WAITING: {RUNNING, CANCELLED, FAILED},
        COMPLETED: set(),
        CANCELLED: set(),
        FAILED: set(),
    }

    def __init__(self) -> None:
        self._states: Dict[str, AgentState] = {}

    def create(self, mission_id: str) -> AgentState:
        state = AgentState(mission_id=mission_id, state=CREATED)
        self._states[mission_id] = state
        return state

    def current(self, mission_id: str) -> Optional[AgentState]:
        return self._states.get(mission_id)

    def can_transition(self, mission_id: str, to_state: str) -> bool:
        current = self._states.get(mission_id)
        if current is None:
            return False
        if to_state not in ALL_STATES:
            return False
        return to_state in self.ALLOWED.get(current.state, set())

    def transition(self, mission_id: str, to_state: str) -> TransitionResult:
        current = self._states.get(mission_id)
        if current is None:
            return TransitionResult(
                mission_id=mission_id, allowed=False, reason="mission not created"
            )
        if to_state == current.state:
            return TransitionResult(
                mission_id=mission_id, allowed=False,
                from_state=current.state, to_state=to_state,
                reason="no-op transition (same state)",
            )
        if to_state not in ALL_STATES:
            return TransitionResult(
                mission_id=mission_id, allowed=False,
                from_state=current.state, to_state=to_state,
                reason=f"invalid state {to_state}",
            )
        if current.is_terminal():
            return TransitionResult(
                mission_id=mission_id, allowed=False,
                from_state=current.state, to_state=to_state,
                reason="terminal state, no transition",
            )
        if to_state not in self.ALLOWED.get(current.state, set()):
            return TransitionResult(
                mission_id=mission_id, allowed=False,
                from_state=current.state, to_state=to_state,
                reason=f"transition {current.state}->{to_state} not allowed",
            )
        new_state = AgentState(mission_id=mission_id, state=to_state)
        self._states[mission_id] = new_state
        return TransitionResult(
            mission_id=mission_id, allowed=True,
            from_state=current.state, to_state=to_state, reason="ok",
        )

    def reset(self, mission_id: str) -> bool:
        """Reset ke Created (opsional). Tidak mengubah aturan lain."""
        if mission_id in self._states:
            self._states[mission_id] = AgentState(mission_id=mission_id, state=CREATED)
            return True
        return False


__all__ = ["StateMachine", "TransitionResult", "AgentState"]
