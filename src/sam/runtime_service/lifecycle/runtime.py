"""LifecycleRuntime (Sprint 264).

Program D - Runtime Services & Deployment.
Mengorkestrasi lifecycle sebuah service. Sync, deterministic.
"""
from __future__ import annotations

from .history import LifecycleHistory
from .state import LifecycleState
from .transition import LifecycleTransition
from .validator import LifecycleValidator


class LifecycleRuntime:
    """Runtime lifecycle service (sync, deterministic)."""

    def __init__(self, initial: LifecycleState = None) -> None:
        self._validator = LifecycleValidator()
        self._history = LifecycleHistory()
        self._current = initial or LifecycleState.created()

    @property
    def current(self) -> LifecycleState:
        return self._current

    @property
    def status(self) -> str:
        return self._current.name

    def transition(self, target: LifecycleState) -> LifecycleState:
        self._validator.assert_valid(self._current, target)
        transition = LifecycleTransition(source=self._current, target=target)
        self._history.append(transition)
        self._current = target
        return self._current

    def history(self) -> list:
        return [
            {"source": t.source.name, "target": t.target.name}
            for t in self._history.entries()
        ]

    def next_states(self) -> list:
        return self._validator.next_states(self._current)
