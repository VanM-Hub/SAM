"""Agent State — state lifecycle agent (Sprint 158).

State machine Agent Runtime. State: Created, Preparing, Running, Waiting,
Completed, Cancelled, Failed. Tidak ada auto retry.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set

# State yang valid
CREATED = "Created"
PREPARING = "Preparing"
RUNNING = "Running"
WAITING = "Waiting"
COMPLETED = "Completed"
CANCELLED = "Cancelled"
FAILED = "Failed"

ALL_STATES: Set[str] = {
    CREATED, PREPARING, RUNNING, WAITING, COMPLETED, CANCELLED, FAILED,
}

TERMINAL_STATES: Set[str] = {COMPLETED, CANCELLED, FAILED}


@dataclass(frozen=True)
class AgentState:
    """State agent mission (immutable)."""
    mission_id: str
    state: str = CREATED
    detail: str = ""

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def is_valid_state(self) -> bool:
        return self.state in ALL_STATES
