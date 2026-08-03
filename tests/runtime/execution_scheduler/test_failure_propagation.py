"""Tests: ADR-004 Linear Failure Propagation.

Failure propagates linearly forward.
No feedback loop, no retry, no recovery, no circuit breaker.
"""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionLifecycleState,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResultState,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    ExecutionNotFoundError,
    InvalidTransitionError,
    NotOperationalError,
    InvalidApprovalError,
    ExecutionConflictError,
)


class TestFailurePropagation:
    """Tests that failure behavior follows ADR-004: linear forward only."""

    def test_failure_reaches_terminal_state(self):
        """A failing execution reaches a terminal state (FAILED then ARCHIVED)."""
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        svc.transition(identity.execution_id, "FAILED")

        r = svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.FAILED
        assert r.result is not None
        assert r.result.state == ExecutionResultState.FAILED

        # Can archive after failure
        svc.transition(identity.execution_id, "ARCHIVED")
        r = svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.ARCHIVED

    def test_no_retry_mechanism(self):
        """ADR-004: no retry policy. No automatic retry."""
        # The scheduler itself has no retry mechanism.
        # This test confirms that after FAILED → ARCHIVED, no further
        # transitions are possible (terminal).
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        svc.transition(identity.execution_id, "FAILED")
        svc.transition(identity.execution_id, "ARCHIVED")

        # No further transitions from ARCHIVED
        with pytest.raises(InvalidTransitionError):
            svc.transition(identity.execution_id, "QUEUED")

    def test_failure_no_recovery_path(self):
        """Cannot go from FAILED back to QUEUED or RUNNING."""
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        svc.transition(identity.execution_id, "FAILED")

        # Cannot "recover" from FAILED
        with pytest.raises(InvalidTransitionError):
            svc.transition(identity.execution_id, "QUEUED")
        with pytest.raises(InvalidTransitionError):
            svc.transition(identity.execution_id, "RUNNING")

    def test_failure_is_observable(self):
        """EXECUTION_SPEC: all failures are observable."""
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        svc.transition(identity.execution_id, "FAILED")

        r = svc.get(identity.execution_id)
        d = r.to_dict()
        assert d["lifecycle_state"] == "FAILED"
        assert d["result"] == "FAILED"

    def test_cancelled_path(self):
        """Cancelled execution also follows linear propagation."""
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.transition(identity.execution_id, "CANCELLED")
        r = svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.CANCELLED
        assert r.result.state == ExecutionResultState.CANCELLED

    def test_timed_out_path(self):
        """Timed Out execution follows linear propagation."""
        svc = SchedulerService()
        svc.initialize()

        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        svc.transition(identity.execution_id, "TIMED_OUT")

        r = svc.get(identity.execution_id)
        assert r.lifecycle_state == ExecutionLifecycleState.TIMED_OUT
        assert r.result.state == ExecutionResultState.TIMED_OUT

    def test_failure_does_not_feedback(self):
        """ADR-004: Audit does not feed back. No feedback loop exists in scheduler."""
        # The Execution Scheduler has no feedback mechanism — it only
        # propagates forward. This is verified by the fact that there's
        # no method to "receive feedback" from downstream.
        svc = SchedulerService()
        svc.initialize()

        # The public API only supports forward movement
        allowed = {"create_execution", "schedule", "transition", "verify", "get",
                   "get_health"}
        from src.sam.runtime.execution_scheduler.interfaces.scheduler_interface import (
            ExecutionSchedulerInterface,
        )
        # Protocol methods must match authorized entry points
        proto_methods = {
            name for name, _ in ExecutionSchedulerInterface.__dict__.items()
            if not name.startswith("_") and callable(_)
        }
        assert proto_methods == allowed
