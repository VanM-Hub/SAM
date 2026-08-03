"""Tests: SchedulerService — create_execution, schedule, transition, verify, get.

Covers all 6 public API methods.
"""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
    ExecutionResultState,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionLifecycleState,
    ExecutionStateRecord,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    ExecutionNotFoundError,
    InvalidTransitionError,
    InvalidApprovalError,
    NotOperationalError,
    MissingContractError,
    InvalidExecutionRequestError,
    ExecutionConflictError,
    VerificationFailureError,
)
from src.sam.runtime.contracts import ContractIdempotency


@pytest.fixture
def running_svc():
    svc = SchedulerService()
    svc.initialize()
    return svc


@pytest.fixture
def valid_request():
    return ExecutionRequest(
        approval_reference="appr-001",
        contract_reference="ctr-001",
        capability_reference="cap-001",
    )


# ──────────────────────────────────────────────
# create_execution
# ──────────────────────────────────────────────

class TestCreateExecution:
    def test_create_with_valid_request(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request,
            approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.IDEMPOTENT.value,
        )
        assert identity.execution_id is not None
        assert identity.approval_reference == "appr-001"
        assert identity.contract_reference == "ctr-001"
        assert identity.capability_reference == "cap-001"

    def test_create_generates_unique_ids(self, running_svc, valid_request):
        id1 = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        id2 = running_svc.create_execution(
            ExecutionRequest("appr-002", "ctr-002", "cap-002"),
            approval_state="APPROVED",
        )
        assert id1.execution_id != id2.execution_id

    def test_created_execution_in_created_state(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        record = running_svc.get(identity.execution_id)
        assert record.lifecycle_state == ExecutionLifecycleState.CREATED

    def test_create_invalid_request_raises(self, running_svc):
        req = ExecutionRequest("", "c1", "cp1")
        with pytest.raises(InvalidExecutionRequestError):
            running_svc.create_execution(req, approval_state="APPROVED")

    def test_create_not_approved_raises(self, running_svc, valid_request):
        with pytest.raises(InvalidApprovalError):
            running_svc.create_execution(valid_request, approval_state="REJECTED")

    def test_create_not_operational_raises(self, valid_request):
        svc = SchedulerService()
        with pytest.raises(NotOperationalError):
            svc.create_execution(valid_request, approval_state="APPROVED")

    def test_create_without_approval_state_ok(self, running_svc, valid_request):
        """Creating without providing approval_state doesn't validate."""
        identity = running_svc.create_execution(valid_request)
        assert identity is not None

    def test_create_sets_sequence_number(self, running_svc, valid_request):
        id1 = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        id2 = running_svc.create_execution(
            ExecutionRequest("appr-002", "ctr-002", "cap-002"),
            approval_state="APPROVED",
        )
        r1 = running_svc.get(id1.execution_id)
        r2 = running_svc.get(id2.execution_id)
        assert r1.sequence_number < r2.sequence_number

    def test_create_with_default_idempotency(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        assert identity is not None


# ──────────────────────────────────────────────
# schedule
# ──────────────────────────────────────────────

class TestSchedule:
    def test_schedule_created_to_queued(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.schedule(identity.execution_id)
        record = running_svc.get(identity.execution_id)
        assert record.lifecycle_state == ExecutionLifecycleState.QUEUED

    def test_schedule_nonexistent_raises(self, running_svc):
        with pytest.raises(ExecutionNotFoundError):
            running_svc.schedule("nonexistent")

    def test_schedule_not_operational_raises(self, valid_request):
        svc = SchedulerService()
        with pytest.raises(NotOperationalError):
            svc.schedule("any")


# ──────────────────────────────────────────────
# transition
# ──────────────────────────────────────────────

class TestTransition:
    def test_transition_created_to_queued(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.transition(identity.execution_id, "QUEUED")
        record = running_svc.get(identity.execution_id)
        assert record.lifecycle_state == ExecutionLifecycleState.QUEUED

    def test_transition_nonexistent_raises(self, running_svc):
        with pytest.raises(ExecutionNotFoundError):
            running_svc.transition("nonexistent", "QUEUED")

    def test_transition_invalid_raises(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        with pytest.raises(InvalidTransitionError):
            running_svc.transition(identity.execution_id, "archived")

    def test_transition_unknown_state_raises(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        with pytest.raises(InvalidTransitionError):
            running_svc.transition(identity.execution_id, "UNDERWATER")

    def test_transition_uppercase_normalized(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.transition(identity.execution_id, "queued")  # lowercase
        record = running_svc.get(identity.execution_id)
        assert record.lifecycle_state == ExecutionLifecycleState.QUEUED


# ──────────────────────────────────────────────
# verify
# ──────────────────────────────────────────────

class TestVerify:
    def test_verify_valid_execution(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        result = running_svc.verify(identity.execution_id)
        assert result["verified"] is True

    def test_verify_nonexistent_raises(self, running_svc):
        with pytest.raises(ExecutionNotFoundError):
            running_svc.verify("nonexistent")

    def test_verify_stores_timestamp(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.verify(identity.execution_id)
        record = running_svc.get(identity.execution_id)
        assert "verification_timestamp" in record.metadata
        assert record.metadata["verified"] is True


# ──────────────────────────────────────────────
# get
# ──────────────────────────────────────────────

class TestGet:
    def test_get_existing(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        record = running_svc.get(identity.execution_id)
        assert record.identity.execution_id == identity.execution_id

    def test_get_nonexistent_raises(self, running_svc):
        with pytest.raises(ExecutionNotFoundError):
            running_svc.get("nonexistent")


# ──────────────────────────────────────────────
# get_health
# ──────────────────────────────────────────────

class TestGetHealth:
    def test_running_is_available(self, running_svc):
        health = running_svc.get_health()
        assert health["status"] == "available"
        assert health["operational"] is True

    def test_after_shutdown_is_unavailable(self, running_svc):
        running_svc.shutdown()
        health = running_svc.get_health()
        assert health["status"] == "unavailable"
        assert health["operational"] is False


# ──────────────────────────────────────────────
# Full workflow
# ──────────────────────────────────────────────

class TestFullWorkflow:
    def test_full_execution_pipeline(self, running_svc, valid_request):
        """Complete path: create → schedule → run → complete → archive."""
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )

        # Schedule
        running_svc.schedule(identity.execution_id)
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.QUEUED

        # Run
        running_svc.transition(identity.execution_id, "RUNNING")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.RUNNING

        # Complete
        running_svc.transition(identity.execution_id, "COMPLETED")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.COMPLETED
        assert r.result is not None
        assert r.result.state == ExecutionResultState.COMPLETED

        # Archive
        running_svc.transition(identity.execution_id, "ARCHIVED")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_multiple_executions_independent(self, running_svc, valid_request):
        req2 = ExecutionRequest("appr-002", "ctr-002", "cap-002")
        id1 = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        id2 = running_svc.create_execution(
            req2, approval_state="APPROVED",
        )
        assert id1.execution_id != id2.execution_id
        assert running_svc.record_count == 2

    def test_shutdown_prevents_new_executions(self, running_svc, valid_request):
        running_svc.shutdown()
        with pytest.raises(NotOperationalError):
            running_svc.create_execution(
                valid_request, approval_state="APPROVED",
            )

    def test_failure_path(self, running_svc, valid_request):
        """Failure path: create → schedule → run → fail → archive."""
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.schedule(identity.execution_id)
        running_svc.transition(identity.execution_id, "RUNNING")
        running_svc.transition(identity.execution_id, "FAILED")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.FAILED
        assert r.result.state == ExecutionResultState.FAILED

        running_svc.transition(identity.execution_id, "ARCHIVED")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_cancelled_path(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.transition(identity.execution_id, "CANCELLED")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.CANCELLED
        assert r.result.state == ExecutionResultState.CANCELLED

    def test_timed_out_path(self, running_svc, valid_request):
        identity = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        running_svc.schedule(identity.execution_id)
        running_svc.transition(identity.execution_id, "RUNNING")
        running_svc.transition(identity.execution_id, "TIMED_OUT")
        r = running_svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.TIMED_OUT
        assert r.result.state == ExecutionResultState.TIMED_OUT

    def test_list_executions(self, running_svc, valid_request):
        id1 = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        id2 = running_svc.create_execution(
            ExecutionRequest("appr-002", "ctr-002", "cap-002"),
            approval_state="APPROVED",
        )
        executions = running_svc.list_executions()
        assert len(executions) == 2

    def test_list_executions_by_sequence(self, running_svc, valid_request):
        id1 = running_svc.create_execution(
            valid_request, approval_state="APPROVED",
        )
        id2 = running_svc.create_execution(
            ExecutionRequest("appr-002", "ctr-002", "cap-002"),
            approval_state="APPROVED",
        )
        sorted_execs = running_svc.list_executions_by_sequence()
        assert sorted_execs[0].sequence_number < sorted_execs[1].sequence_number
