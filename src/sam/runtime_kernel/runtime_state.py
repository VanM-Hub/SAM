"""Runtime State — frozen DTOs state runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuntimeState:
    state_id: str
    state: str = "initial"
    previous_state: str = ""
    subsystem: str = "runtime_kernel"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StateMachine:
    machine_id: str
    states: Dict[str, str] = field(default_factory=dict)
    current_state: str = "initial"


@dataclass(frozen=True)
class StateSnapshot:
    snapshot_id: str
    timestamp: float
    state: str
    components: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StateHistoryEntry:
    entry_id: str
    state: str
    transition: str = ""
    timestamp: float = 0.0


@dataclass(frozen=True)
class StateValidation:
    validation_id: str
    valid: bool = True
    errors: List[str] = field(default_factory=list)
