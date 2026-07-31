"""LifecycleValidator (Sprint 264).

Program D - Runtime Services & Deployment.
Validator transisi lifecycle (deterministik).
"""
from __future__ import annotations
from typing import List

from .state import LifecycleState
from .transition import LifecycleTransition


class LifecycleValidator:
    """Validator transisi lifecycle (sync, deterministic)."""

    def can_transition(self, source: LifecycleState,
                       target: LifecycleState) -> bool:
        return LifecycleTransition(source=source, target=target).is_valid()

    def assert_valid(self, source: LifecycleState,
                     target: LifecycleState) -> None:
        if not self.can_transition(source, target):
            raise ValueError(
                f"invalid transition: {source.name} -> {target.name}"
            )

    def next_states(self, state: LifecycleState) -> List[str]:
        from .transition import _TRANSITIONS
        return list(_TRANSITIONS.get(state.name, ()))
