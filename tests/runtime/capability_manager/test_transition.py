"""Tests for LifecycleService + LifecycleValidator.

Verifies: transition flow, validation, error handling.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import CapabilityLifecycle
from sam.runtime.capability_manager.services.lifecycle_service import (
    LifecycleService,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidTransition,
    CapabilityNotFound,
)


class TestLifecycleService:
    """Tests for LifecycleService — transition orchestration."""

    def setup_method(self) -> None:
        self.service = LifecycleService()
        self.service.register("memory.lookup", CapabilityLifecycle.DECLARED)

    def test_register_and_get_state(self) -> None:
        """Register stores and get_state retrieves."""
        assert self.service.get_state("memory.lookup") == CapabilityLifecycle.DECLARED

    def test_get_state_missing_raises(self) -> None:
        """get_state raises CapabilityNotFound for unknown identity."""
        with pytest.raises(CapabilityNotFound):
            self.service.get_state("nonexistent")

    def test_valid_transition_declared_to_registered(self) -> None:
        """DECLARED → REGISTERED succeeds."""
        result = self.service.transition(
            "memory.lookup",
            CapabilityLifecycle.REGISTERED,
        )
        assert result.success is True
        assert result.from_state == CapabilityLifecycle.DECLARED
        assert result.to_state == CapabilityLifecycle.REGISTERED
        assert self.service.get_state("memory.lookup") == CapabilityLifecycle.REGISTERED

    def test_invalid_transition_declared_to_available(self) -> None:
        """DECLARED → AVAILABLE (skip steps) fails."""
        with pytest.raises(InvalidTransition):
            self.service.transition(
                "memory.lookup",
                CapabilityLifecycle.AVAILABLE,
            )

    def test_full_lifecycle_path(self) -> None:
        """Complete DECLARED → ... → RETIRED path."""
        path = [
            CapabilityLifecycle.REGISTERED,
            CapabilityLifecycle.CERTIFIED,
            CapabilityLifecycle.AVAILABLE,
            CapabilityLifecycle.DEPRECATED,
            CapabilityLifecycle.RETIRED,
        ]
        current = CapabilityLifecycle.DECLARED
        for target in path:
            result = self.service.transition("memory.lookup", target)
            assert result.success is True
            assert result.from_state == current
            assert result.to_state == target
            current = target
        # RETIRED is terminal
        with pytest.raises(InvalidTransition):
            self.service.transition(
                "memory.lookup",
                CapabilityLifecycle.AVAILABLE,
            )

    def test_deprecated_back_to_available(self) -> None:
        """DEPRECATED can return to AVAILABLE (recovery)."""
        # Go to DEPRECATED
        for state in [
            CapabilityLifecycle.REGISTERED,
            CapabilityLifecycle.CERTIFIED,
            CapabilityLifecycle.AVAILABLE,
            CapabilityLifecycle.DEPRECATED,
        ]:
            self.service.transition("memory.lookup", state)
        assert self.service.get_state("memory.lookup") == CapabilityLifecycle.DEPRECATED

        # Recover to AVAILABLE
        result = self.service.transition(
            "memory.lookup",
            CapabilityLifecycle.AVAILABLE,
        )
        assert result.success is True
        assert result.to_state == CapabilityLifecycle.AVAILABLE

    def test_same_state_transition_is_valid(self) -> None:
        """Transitioning to the same state is a valid no-op."""
        result = self.service.transition(
            "memory.lookup",
            CapabilityLifecycle.DECLARED,
        )
        assert result.success is True
        assert result.from_state == result.to_state

    def test_retired_is_terminal(self) -> None:
        """Cannot transition from RETIRED."""
        # Reach RETIRED
        path = [
            CapabilityLifecycle.REGISTERED,
            CapabilityLifecycle.CERTIFIED,
            CapabilityLifecycle.AVAILABLE,
            CapabilityLifecycle.DEPRECATED,
            CapabilityLifecycle.RETIRED,
        ]
        for target in path:
            self.service.transition("memory.lookup", target)

        with pytest.raises(InvalidTransition):
            self.service.transition(
                "memory.lookup",
                CapabilityLifecycle.AVAILABLE,
            )
