"""LifecycleCheck — verifies lifecycle state transitions are valid.

Deterministic: same lifecycle + same states → same result.
Useful for verifying engine/component lifecycle compliance.
"""

from __future__ import annotations

from typing import Dict, List, Set

from ..base.base_check import BaseComplianceCheck
from ..base.check_context import CheckContext
from ..base.check_result import CheckResult


class LifecycleCheck(BaseComplianceCheck):
    """Checks that a sequence of state transitions is valid.

    Config fields:
        transitions: Dict[str, List[str]] — valid transition map.
                     Key = current state, Value = allowed next states.
        history: List[str] — the state transition history to validate (optional).
        initial_state: str — expected initial state.
        terminal_state: str — expected terminal state.

    The history is validated pairwise: each pair (prev, next) must
    exist in the transitions map. If history is not provided or empty,
    only the initial_state and terminal_state presence is checked.
    """

    def __init__(
        self,
        transitions: Dict[str, List[str]],
        history: List[str] = None,
        initial_state: str = None,
        terminal_state: str = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._transitions = {k: set(v) for k, v in transitions.items()}
        self._history = list(history) if history else []
        self._initial_state = initial_state
        self._terminal_state = terminal_state

    def execute(self, context: CheckContext) -> CheckResult:
        errors = []

        # Check initial state
        if self._initial_state is not None:
            if not self._history:
                errors.append(
                    "Expected initial state '%s' but history is empty"
                    % self._initial_state
                )
            elif self._history[0] != self._initial_state:
                errors.append(
                    "Expected initial state '%s' but found '%s'"
                    % (self._initial_state, self._history[0])
                )

        # Check pairwise transitions
        for i in range(len(self._history) - 1):
            prev = self._history[i]
            nxt = self._history[i + 1]

            if prev not in self._transitions:
                errors.append(
                    "State '%s' has no defined transitions" % prev
                )
            elif nxt not in self._transitions[prev]:
                errors.append(
                    "Invalid transition: '%s' → '%s' (allowed: %s)"
                    % (prev, nxt, ", ".join(sorted(self._transitions[prev])))
                )

        # Check terminal state
        if self._terminal_state is not None:
            if not self._history:
                errors.append(
                    "Expected terminal state '%s' but history is empty"
                    % self._terminal_state
                )
            elif self._history[-1] != self._terminal_state:
                errors.append(
                    "Expected terminal state '%s' but found '%s'"
                    % (self._terminal_state, self._history[-1])
                )

        if not errors:
            return CheckResult.success(
                details="All %d transition(s) are valid for history of length %d"
                % (max(0, len(self._history) - 1), len(self._history)),
                evidence={
                    "history": self._history,
                    "transitions": {k: sorted(v) for k, v in self._transitions.items()},
                    "errors": [],
                },
            )

        return CheckResult.failure(
            details="%d transition error(s): %s" % (len(errors), "; ".join(errors)),
            evidence={
                "history": self._history,
                "transitions": {k: sorted(v) for k, v in self._transitions.items()},
                "errors": errors,
                "error_count": len(errors),
            },
        )

    def to_config(self) -> dict:
        config = super().to_config()
        config["transitions"] = {k: sorted(v) for k, v in self._transitions.items()}
        config["history"] = list(self._history)
        if self._initial_state:
            config["initial_state"] = self._initial_state
        if self._terminal_state:
            config["terminal_state"] = self._terminal_state
        return config
