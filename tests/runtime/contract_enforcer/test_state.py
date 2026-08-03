"""Tests for ContractState machine.

Authority: I2-004 §4
"""

import pytest

from sam.runtime.contract_enforcer.state.contract_state import (
    ContractState,
    ContractOperationState,
)


class TestContractState:
    """Tests for ContractState."""

    def setup_method(self) -> None:
        self.state = ContractState()

    def test_initial_state_is_created(self) -> None:
        """New state starts at CREATED."""
        assert self.state.state == ContractOperationState.CREATED

    def test_created_to_validating(self) -> None:
        """CREATED → VALIDATING is allowed."""
        self.state.transition_to(ContractOperationState.VALIDATING)
        assert self.state.state == ContractOperationState.VALIDATING

    def test_validating_to_valid(self) -> None:
        """VALIDATING → VALID is allowed."""
        self.state.transition_to(ContractOperationState.VALIDATING)
        self.state.transition_to(ContractOperationState.VALID)
        assert self.state.state == ContractOperationState.VALID

    def test_validating_to_invalid(self) -> None:
        """VALIDATING → INVALID is allowed."""
        self.state.transition_to(ContractOperationState.VALIDATING)
        self.state.transition_to(ContractOperationState.INVALID)
        assert self.state.state == ContractOperationState.INVALID

    def test_valid_to_negotiating(self) -> None:
        """VALID → NEGOTIATING is allowed."""
        self.state.transition_to(ContractOperationState.VALIDATING)
        self.state.transition_to(ContractOperationState.VALID)
        self.state.transition_to(ContractOperationState.NEGOTIATING)
        assert self.state.state == ContractOperationState.NEGOTIATING

    def test_negotiating_to_negotiated(self) -> None:
        """NEGOTIATING → NEGOTIATED is allowed."""
        self._goto_negotiating()
        self.state.transition_to(ContractOperationState.NEGOTIATED)
        assert self.state.state == ContractOperationState.NEGOTIATED

    def test_negotiating_to_failed(self) -> None:
        """NEGOTIATING → FAILED is allowed."""
        self._goto_negotiating()
        self.state.transition_to(ContractOperationState.FAILED)
        assert self.state.state == ContractOperationState.FAILED

    def test_invalid_is_terminal(self) -> None:
        """INVALID is terminal."""
        self.state.transition_to(ContractOperationState.VALIDATING)
        self.state.transition_to(ContractOperationState.INVALID)
        assert self.state.is_terminal() is True
        with pytest.raises(ValueError):
            self.state.transition_to(ContractOperationState.VALID)

    def test_negotiated_is_terminal(self) -> None:
        """NEGOTIATED is terminal."""
        self._goto_negotiating()
        self.state.transition_to(ContractOperationState.NEGOTIATED)
        assert self.state.is_terminal() is True

    def test_failed_is_terminal(self) -> None:
        """FAILED is terminal."""
        self._goto_negotiating()
        self.state.transition_to(ContractOperationState.FAILED)
        assert self.state.is_terminal() is True

    def test_is_valid_method(self) -> None:
        """is_valid() returns True for VALID states."""
        assert self.state.is_valid() is False  # CREATED
        self.state.transition_to(ContractOperationState.VALIDATING)
        assert self.state.is_valid() is False  # VALIDATING
        self.state.transition_to(ContractOperationState.VALID)
        assert self.state.is_valid() is True  # VALID

    def test_same_state_noop(self) -> None:
        """Transition to same state is no-op."""
        self.state.transition_to(ContractOperationState.CREATED)
        assert self.state.state == ContractOperationState.CREATED

    def test_invalid_skip(self) -> None:
        """CREATED → VALID (skip) not allowed."""
        with pytest.raises(ValueError):
            self.state.transition_to(ContractOperationState.VALID)

    def _goto_negotiating(self) -> None:
        self.state.transition_to(ContractOperationState.VALIDATING)
        self.state.transition_to(ContractOperationState.VALID)
        self.state.transition_to(ContractOperationState.NEGOTIATING)
