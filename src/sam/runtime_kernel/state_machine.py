"""State Machine — FSM runtime."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_state import StateMachine


class StateMachineEngine:
    """Engine state machine — preview-only."""

    ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
        "initial": ["booting", "shutdown"],
        "booting": ["ready", "failed"],
        "ready": ["active", "suspended", "shutdown"],
        "active": ["ready", "suspended", "shutdown"],
        "suspended": ["ready", "shutdown"],
        "failed": ["booting", "shutdown"],
        "shutdown": ["initial"],
    }

    def __init__(self) -> None:
        self._machines: Dict[str, StateMachine] = {}

    def create(self, machine_id: str, initial: str = "initial") -> StateMachine:
        m = StateMachine(machine_id=machine_id, states={}, current_state=initial)
        self._machines[machine_id] = m
        return m

    def transition(self, machine_id: str, new_state: str) -> StateMachine | None:
        m = self._machines.get(machine_id)
        if not m:
            return None

        allowed = self.ALLOWED_TRANSITIONS.get(m.current_state, [])
        if new_state not in allowed:
            return None

        new_states = dict(m.states)
        new_states[m.current_state] = new_state

        m2 = StateMachine(
            machine_id=m.machine_id,
            states=new_states,
            current_state=new_state,
        )
        self._machines[machine_id] = m2
        return m2

    def can_transition(self, machine_id: str, target: str) -> bool:
        m = self._machines.get(machine_id)
        if not m:
            return False
        return target in self.ALLOWED_TRANSITIONS.get(m.current_state, [])

    def get(self, machine_id: str) -> StateMachine | None:
        return self._machines.get(machine_id)
