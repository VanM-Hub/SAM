"""Tests: ADR-005 Strict Linear Ordering.

Approval-arrival order = Execution order.
No bypass, one operation reaches terminal before next.
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
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    OrderingViolationError,
)
from src.sam.runtime.execution_scheduler.validation.ordering_validator import (
    OrderingValidator,
)


class TestSequenceNumbering:
    def test_first_execution_gets_seq_1(self):
        svc = SchedulerService()
        svc.initialize()
        req = ExecutionRequest("a1", "c1", "cp1")
        identity = svc.create_execution(req, approval_state="APPROVED")
        record = svc.get(identity.execution_id)
        assert record.sequence_number == 1

    def test_sequential_numbering(self):
        svc = SchedulerService()
        svc.initialize()
        ids = []
        for i in range(5):
            req = ExecutionRequest(f"a{i}", f"c{i}", f"cp{i}")
            identity = svc.create_execution(req, approval_state="APPROVED")
            ids.append(identity)
        seqs = [svc.get(eid.execution_id).sequence_number for eid in ids]
        assert seqs == [1, 2, 3, 4, 5]

    def test_list_by_sequence(self):
        svc = SchedulerService()
        svc.initialize()
        for i in range(3):
            req = ExecutionRequest(f"a{i}", f"c{i}", f"cp{i}")
            svc.create_execution(req, approval_state="APPROVED")
        sorted_execs = svc.list_executions_by_sequence()
        assert sorted_execs[0].sequence_number == 1
        assert sorted_execs[1].sequence_number == 2
        assert sorted_execs[2].sequence_number == 3


class TestOrderingEnforcement:
    def test_schedule_respects_sequence(self):
        """First execution can schedule since it has lowest seq."""
        svc = SchedulerService()
        svc.initialize()
        id1 = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"), approval_state="APPROVED",
        )
        id2 = svc.create_execution(
            ExecutionRequest("a2", "c2", "cp2"), approval_state="APPROVED",
        )
        # Execution 1 (seq=1) should be schedulable
        svc.schedule(id1.execution_id)
        record = svc.get(id1.execution_id)
        assert record.lifecycle_state == ExecutionLifecycleState.QUEUED

    def test_ordering_validator_rejects_out_of_order(self):
        """An execution with higher seq cannot proceed if lower-seq is not finished."""
        svc = SchedulerService()
        svc.initialize()
        id1 = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"), approval_state="APPROVED",
        )
        id2 = svc.create_execution(
            ExecutionRequest("a2", "c2", "cp2"), approval_state="APPROVED",
        )
        r1 = svc.get(id1.execution_id)
        r2 = svc.get(id2.execution_id)
        all_records = svc.list_executions()

        # r1 (seq=1) should pass
        assert OrderingValidator.validate_order(r1, all_records) is True

        # r2 (seq=2) should fail because r1 is still CREATED (not at result state)
        with pytest.raises(ValueError, match="Ordering violation"):
            OrderingValidator.validate_order(r2, all_records)

    def test_ordering_passes_when_earlier_is_completed(self):
        """After seq=1 is completed, seq=2 can proceed."""
        svc = SchedulerService()
        svc.initialize()
        id1 = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"), approval_state="APPROVED",
        )
        id2 = svc.create_execution(
            ExecutionRequest("a2", "c2", "cp2"), approval_state="APPROVED",
        )

        # Complete first execution
        r1 = svc.get(id1.execution_id)
        svc.schedule(id1.execution_id)
        svc.transition(id1.execution_id, "RUNNING")
        svc.transition(id1.execution_id, "COMPLETED")

        # Now r2 should pass
        r2 = svc.get(id2.execution_id)
        all_records = svc.list_executions()
        assert OrderingValidator.validate_order(r2, all_records) is True

    def test_get_next_sequence_empty(self):
        assert OrderingValidator.get_next_sequence([]) == 1

    def test_get_next_sequence_non_empty(self):
        svc = SchedulerService()
        svc.initialize()
        svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"), approval_state="APPROVED",
        )
        svc.create_execution(
            ExecutionRequest("a2", "c2", "cp2"), approval_state="APPROVED",
        )
        next_seq = OrderingValidator.get_next_sequence(svc.list_executions())
        assert next_seq == 3


class TestNoBypass:
    def test_cannot_bypass_unfinished_execution(self):
        """Scheduler enforces that earlier executions must complete first."""
        svc = SchedulerService()
        svc.initialize()
        id1 = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"), approval_state="APPROVED",
        )
        id2 = svc.create_execution(
            ExecutionRequest("a2", "c2", "cp2"), approval_state="APPROVED",
        )

        # Schedule id1, but DON'T complete it
        svc.schedule(id1.execution_id)

        # Try scheduling id2 — should fail because id1 is QUEUED (not result state)
        with pytest.raises(OrderingViolationError):
            svc.schedule(id2.execution_id)
