# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: conversation_state.

Read-only conversation bridge for mission state.
"""
from __future__ import annotations

from typing import Dict, Optional

from .mission_state import MissionState
from .state_registry import StateRegistry
from .state_transition import StateTransition
from .state_history import StateHistory


class ConversationStateBridge:
    """Read-only bridge exposing mission state."""

    def __init__(self, registry: StateRegistry, history: StateHistory) -> None:
        self._registry = registry
        self._history = history

    def open(self, mission_id: str) -> MissionState:
        state = MissionState(mission_id=mission_id, state="open")
        self._registry.set(state)
        return state

    def transition(self, mission_id: str, to_state: str) -> StateTransition:
        current = self._registry.get(mission_id)
        from_state = current.state if current else "open"
        t = StateTransition(mission_id=mission_id, from_state=from_state, to_state=to_state)
        self._registry.set(MissionState(mission_id=mission_id, state=to_state))
        self._history.record(t)
        return t

    def state_of(self, mission_id: str) -> Optional[MissionState]:
        return self._registry.get(mission_id)

    def summary(self) -> Dict[str, int]:
        return {"missions": self._registry.count(), "transitions": self._history.count()}
