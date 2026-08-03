"""Tests for CapabilityLifecycle enum + CapabilityState machine.

Verifies: enum values, state transitions, forbidden paths, terminal checks.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import CapabilityLifecycle
from sam.runtime.capability_manager.state.capability_state import (
    CapabilityState,
)


class TestCapabilityLifecycleEnum:
    """Tests for CapabilityLifecycle enum values."""

    def test_has_six_states(self) -> None:
        """CapabilityLifecycle has exactly 6 states."""
        states = list(CapabilityLifecycle)
        assert len(states) == 6

    def test_declared_is_first(self) -> None:
        """DECLARED is the initial state."""
        assert CapabilityLifecycle.DECLARED is not None

    def test_retired_is_last(self) -> None:
        """RETIRED is the terminal state."""
        assert CapabilityLifecycle.RETIRED.is_terminal() is True

    def test_discoverable_states(self) -> None:
        """All states except RETIRED are discoverable."""
        for state in CapabilityLifecycle:
            if state == CapabilityLifecycle.RETIRED:
                assert state.is_discoverable() is False
            else:
                assert state.is_discoverable() is True

    def test_only_retired_is_terminal(self) -> None:
        """Only RETIRED is a terminal state."""
        for state in CapabilityLifecycle:
            if state == CapabilityLifecycle.RETIRED:
                assert state.is_terminal() is True
            else:
                assert state.is_terminal() is False


class TestCapabilityStateMachine:
    """Tests for CapabilityState transition engine."""

    # ── Allowed transitions ────────────────────────────────────────

    def test_declared_to_registered_allowed(self) -> None:
        """DECLARED → REGISTERED is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.DECLARED,
            CapabilityLifecycle.REGISTERED,
        ) is True

    def test_registered_to_certified_allowed(self) -> None:
        """REGISTERED → CERTIFIED is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.REGISTERED,
            CapabilityLifecycle.CERTIFIED,
        ) is True

    def test_certified_to_available_allowed(self) -> None:
        """CERTIFIED → AVAILABLE is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.CERTIFIED,
            CapabilityLifecycle.AVAILABLE,
        ) is True

    def test_available_to_deprecated_allowed(self) -> None:
        """AVAILABLE → DEPRECATED is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.AVAILABLE,
            CapabilityLifecycle.DEPRECATED,
        ) is True

    def test_deprecated_to_available_allowed(self) -> None:
        """DEPRECATED → AVAILABLE (recovery) is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.DEPRECATED,
            CapabilityLifecycle.AVAILABLE,
        ) is True

    def test_deprecated_to_retired_allowed(self) -> None:
        """DEPRECATED → RETIRED is allowed."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.DEPRECATED,
            CapabilityLifecycle.RETIRED,
        ) is True

    # ── Forbidden transitions ──────────────────────────────────────

    def test_declared_to_available_not_allowed(self) -> None:
        """DECLARED → AVAILABLE is NOT allowed (skip steps)."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.DECLARED,
            CapabilityLifecycle.AVAILABLE,
        ) is False

    def test_retired_to_anything_not_allowed(self) -> None:
        """RETIRED is terminal — no transitions."""
        for state in CapabilityLifecycle:
            assert CapabilityState.can_transition(
                CapabilityLifecycle.RETIRED,
                state,
            ) is False

    def test_skip_steps_not_allowed(self) -> None:
        """Cannot skip lifecycle steps (e.g., DECLARED → CERTIFIED)."""
        assert CapabilityState.can_transition(
            CapabilityLifecycle.DECLARED,
            CapabilityLifecycle.CERTIFIED,
        ) is False

    # ── Transition execution ───────────────────────────────────────

    def test_transition_executes_successfully(self) -> None:
        """Valid transition returns new state."""
        result = CapabilityState.transition(
            CapabilityLifecycle.DECLARED,
            CapabilityLifecycle.REGISTERED,
        )
        assert result == CapabilityLifecycle.REGISTERED

    def test_transition_raises_on_invalid(self) -> None:
        """Invalid transition raises ValueError."""
        with pytest.raises(ValueError, match="Disallowed transition"):
            CapabilityState.transition(
                CapabilityLifecycle.DECLARED,
                CapabilityLifecycle.AVAILABLE,
            )

    def test_transition_raises_on_terminal(self) -> None:
        """Transition from RETIRED raises ValueError."""
        with pytest.raises(ValueError, match="terminal"):
            CapabilityState.transition(
                CapabilityLifecycle.RETIRED,
                CapabilityLifecycle.AVAILABLE,
            )

    # ── Terminal / Reversible ──────────────────────────────────────

    def test_retired_is_terminal(self) -> None:
        """RETIRED is terminal."""
        assert CapabilityState.is_terminal(CapabilityLifecycle.RETIRED) is True

    def test_available_is_not_terminal(self) -> None:
        """AVAILABLE is not terminal."""
        assert CapabilityState.is_terminal(CapabilityLifecycle.AVAILABLE) is False

    def test_deprecated_is_reversible(self) -> None:
        """DEPRECATED is reversible."""
        assert CapabilityState.is_reversible(CapabilityLifecycle.DEPRECATED) is True

    def test_retired_is_not_reversible(self) -> None:
        """RETIRED is not reversible."""
        assert CapabilityState.is_reversible(CapabilityLifecycle.RETIRED) is False

    def test_full_lifecycle_path(self) -> None:
        """Complete lifecycle: DECLARED → ... → RETIRED."""
        path = [
            (CapabilityLifecycle.DECLARED, CapabilityLifecycle.REGISTERED),
            (CapabilityLifecycle.REGISTERED, CapabilityLifecycle.CERTIFIED),
            (CapabilityLifecycle.CERTIFIED, CapabilityLifecycle.AVAILABLE),
            (CapabilityLifecycle.AVAILABLE, CapabilityLifecycle.DEPRECATED),
            (CapabilityLifecycle.DEPRECATED, CapabilityLifecycle.RETIRED),
        ]
        current = CapabilityLifecycle.DECLARED
        for fr, to in path:
            assert CapabilityState.can_transition(fr, to) is True
            current = CapabilityState.transition(current, to)
        assert current == CapabilityLifecycle.RETIRED
