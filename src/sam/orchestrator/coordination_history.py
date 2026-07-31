# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: coordination_history.

History of coordination events. Sync, in-memory, read-only getters.
"""
from __future__ import annotations

from typing import List, Tuple

from .coordination_state import CoordinationState


class CoordinationHistory:
    """Append-only history of coordination states."""

    def __init__(self) -> None:
        self._events: List[CoordinationState] = []

    def record(self, state: CoordinationState) -> None:
        self._events.append(state)

    def events(self) -> Tuple[CoordinationState, ...]:
        return tuple(self._events)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
