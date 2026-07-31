# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: state_history.

History of mission state transitions. Append-only, sync.
"""
from __future__ import annotations

from typing import List, Tuple

from .state_transition import StateTransition


class StateHistory:
    """Append-only history of state transitions."""

    def __init__(self) -> None:
        self._events: List[StateTransition] = []

    def record(self, transition: StateTransition) -> None:
        self._events.append(transition)

    def events(self) -> Tuple[StateTransition, ...]:
        return tuple(self._events)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
