"""Tests: Execution State — 8-state lifecycle + ExecutionStateRecord."""

import pytest
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionLifecycleState,
    ExecutionStateRecord,
    is_valid_transition,
    is_terminal_state,
    is_result_state,
    LEGAL_TRANSITIONS,
)
from src.sam.runtime.execution_scheduler.models.execution_identity import (
    ExecutionIdentity,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
    ExecutionResultState,
)


@pytest.fixture
def identity():
    return ExecutionIdentity("e1", "a1", "c1", "cp1")


@pytest.fixture
def exec_request():
    return ExecutionRequest("a1", "c1", "cp1")


@pytest.fixture
def record(identity, exec_request):
    return ExecutionStateRecord(identity=identity, request=exec_request)


class TestExecutionLifecycleState:
    def test_has_eight_states(self):
        states = list(ExecutionLifecycleState)
        assert len(states) == 8

    def test_created_is_first(self):
        states = list(ExecutionLifecycleState)
        assert states[0] == ExecutionLifecycleState.CREATED

    def test_archived_is_last(self):
        states = list(ExecutionLifecycleState)
        assert states[-1] == ExecutionLifecycleState.ARCHIVED

    def test_result_states(self):
        assert is_result_state(ExecutionLifecycleState.COMPLETED) is True
        assert is_result_state(ExecutionLifecycleState.FAILED) is True
        assert is_result_state(ExecutionLifecycleState.CANCELLED) is True
        assert is_result_state(ExecutionLifecycleState.TIMED_OUT) is True


class TestExecutionStateTransitions:
    def test_initial_state_is_created(self, record):
        assert record.lifecycle_state == ExecutionLifecycleState.CREATED

    def test_created_to_queued(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        assert record.lifecycle_state == ExecutionLifecycleState.QUEUED

    def test_created_to_cancelled(self, record):
        record.transition(ExecutionLifecycleState.CANCELLED)
        assert record.lifecycle_state == ExecutionLifecycleState.CANCELLED

    def test_queued_to_running(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        assert record.lifecycle_state == ExecutionLifecycleState.RUNNING

    def test_queued_to_cancelled(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.CANCELLED)
        assert record.lifecycle_state == ExecutionLifecycleState.CANCELLED

    def test_running_to_completed(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.COMPLETED)
        assert record.lifecycle_state == ExecutionLifecycleState.COMPLETED

    def test_running_to_failed(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.FAILED)
        assert record.lifecycle_state == ExecutionLifecycleState.FAILED

    def test_running_to_cancelled(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.CANCELLED)
        assert record.lifecycle_state == ExecutionLifecycleState.CANCELLED

    def test_running_to_timed_out(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.TIMED_OUT)
        assert record.lifecycle_state == ExecutionLifecycleState.TIMED_OUT

    def test_completed_to_archived(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.COMPLETED)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        assert record.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_failed_to_archived(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.FAILED)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        assert record.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_cancelled_to_archived(self, record):
        record.transition(ExecutionLifecycleState.CANCELLED)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        assert record.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_timed_out_to_archived(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.TIMED_OUT)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        assert record.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    # Invalid transitions
    def test_invalid_created_to_completed(self, record):
        with pytest.raises(ValueError, match="Invalid transition"):
            record.transition(ExecutionLifecycleState.COMPLETED)

    def test_invalid_created_to_archived(self, record):
        with pytest.raises(ValueError):
            record.transition(ExecutionLifecycleState.ARCHIVED)

    def test_from_archived_is_invalid(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.COMPLETED)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        with pytest.raises(ValueError):
            record.transition(ExecutionLifecycleState.QUEUED)

    def test_archived_is_terminal(self):
        assert is_terminal_state(ExecutionLifecycleState.ARCHIVED) is True

    def test_created_is_not_terminal(self):
        assert is_terminal_state(ExecutionLifecycleState.CREATED) is False

    def test_same_state_is_noop(self, record):
        record.transition(ExecutionLifecycleState.CREATED)
        assert record.lifecycle_state == ExecutionLifecycleState.CREATED

    def test_result_states_has_no_transitions(self):
        """COMPLETED, FAILED, CANCELLED, TIMED_OUT only go to ARCHIVED."""
        for state in [ExecutionLifecycleState.COMPLETED,
                      ExecutionLifecycleState.FAILED,
                      ExecutionLifecycleState.CANCELLED,
                      ExecutionLifecycleState.TIMED_OUT]:
            allowed = LEGAL_TRANSITIONS.get(state, set())
            assert allowed == {ExecutionLifecycleState.ARCHIVED} or allowed == set(), \
                f"State {state} has unexpected transitions: {allowed}"


class TestExecutionStateRecord:
    def test_identity_access(self, record):
        assert record.identity.execution_id == "e1"

    def test_request_access(self, record):
        assert record.request.approval_reference == "a1"

    def test_set_and_get_result(self, record):
        r = ExecutionResult.completed("e1", "done")
        record.set_result(r)
        assert record.result is not None
        assert record.result.state == ExecutionResultState.COMPLETED
        assert record.result.message == "done"

    def test_is_terminal(self, record):
        assert record.is_terminal() is False
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.transition(ExecutionLifecycleState.COMPLETED)
        record.transition(ExecutionLifecycleState.ARCHIVED)
        assert record.is_terminal() is True

    def test_has_result(self, record):
        assert record.has_result() is False
        r = ExecutionResult.completed("e1")
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.set_result(r)
        record.transition(ExecutionLifecycleState.COMPLETED)
        assert record.has_result() is True

    def test_to_dict(self, record):
        record.transition(ExecutionLifecycleState.QUEUED)
        d = record.to_dict()
        assert d["execution_id"] == "e1"
        assert d["lifecycle_state"] == "QUEUED"

    def test_to_dict_with_result(self, record):
        r = ExecutionResult.completed("e1", "ok")
        record.transition(ExecutionLifecycleState.QUEUED)
        record.transition(ExecutionLifecycleState.RUNNING)
        record.set_result(r)
        record.transition(ExecutionLifecycleState.COMPLETED)
        d = record.to_dict()
        assert d["result"] == "COMPLETED"
        assert d["result_message"] == "ok"

    def test_repr(self, record):
        r = repr(record)
        assert "e1" in r
        assert "CREATED" in r

    def test_sequence_number_default(self, record):
        assert record.sequence_number == 0

    def test_sequence_number_custom(self, identity, request):
        record = ExecutionStateRecord(
            identity=identity, request=request, sequence_number=42,
        )
        assert record.sequence_number == 42

    def test_metadata_default(self, record):
        assert record.metadata == {}

    def test_is_valid_transition_function(self):
        assert is_valid_transition(
            ExecutionLifecycleState.CREATED,
            ExecutionLifecycleState.QUEUED,
        ) is True
        assert is_valid_transition(
            ExecutionLifecycleState.CREATED,
            ExecutionLifecycleState.COMPLETED,
        ) is False
