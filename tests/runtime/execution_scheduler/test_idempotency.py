"""Tests: ADR-003 Idempotency Observation.

Contract declares; Execution observes.
- IDEMPOTENT: repeated execution allowed.
- NON_IDEMPOTENT: repeated execution → Execution Conflict.
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
    ExecutionConflictError,
)
from src.sam.runtime.execution_scheduler.validation.idempotency_validator import (
    IdempotencyValidator,
)
from src.sam.runtime.contracts import ContractIdempotency


class TestIdempotencyValidator:
    def test_observe_idempotent(self):
        assert IdempotencyValidator.observe_idempotency(
            ContractIdempotency.IDEMPOTENT,
        ) is True

    def test_observe_non_idempotent(self):
        assert IdempotencyValidator.observe_idempotency(
            ContractIdempotency.NON_IDEMPOTENT,
        ) is False

    def test_is_valid_declaration(self):
        assert IdempotencyValidator.is_idempotent_declaration_valid(
            "IDEMPOTENT",
        ) is True
        assert IdempotencyValidator.is_idempotent_declaration_valid(
            "NON_IDEMPOTENT",
        ) is True
        assert IdempotencyValidator.is_idempotent_declaration_valid(
            "UNKNOWN",
        ) is False


class TestIdempotentRepeat:
    def test_idempotent_repeat_allowed(self):
        """With IDEMPOTENT contract, re-creating same operation is allowed."""
        svc = SchedulerService()
        svc.initialize()

        # Create and complete first execution
        req = ExecutionRequest("appr-001", "ctr-001", "cap-001")
        id1 = svc.create_execution(
            req,
            approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.IDEMPOTENT.value,
        )
        svc.schedule(id1.execution_id)
        svc.transition(id1.execution_id, "RUNNING")
        svc.transition(id1.execution_id, "COMPLETED")

        # Re-create same operation — should be allowed (IDEMPOTENT)
        id2 = svc.create_execution(
            req,
            approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.IDEMPOTENT.value,
        )
        assert id2.execution_id != id1.execution_id
        assert svc.record_count == 2


class TestNonIdempotentRepeat:
    def test_non_idempotent_repeat_raises(self):
        """With NON_IDEMPOTENT contract, re-creating raises ExecutionConflict."""
        svc = SchedulerService()
        svc.initialize()

        req = ExecutionRequest("appr-001", "ctr-001", "cap-001")
        id1 = svc.create_execution(
            req,
            approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        svc.schedule(id1.execution_id)
        svc.transition(id1.execution_id, "RUNNING")
        svc.transition(id1.execution_id, "COMPLETED")

        with pytest.raises(ExecutionConflictError):
            svc.create_execution(
                req,
                approval_state="APPROVED",
                contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
            )

    def test_non_idempotent_new_operation_allowed(self):
        """Different operation with NON_IDEMPOTENT contract is fine."""
        svc = SchedulerService()
        svc.initialize()

        req1 = ExecutionRequest("appr-001", "ctr-001", "cap-001")
        id1 = svc.create_execution(
            req1, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        svc.schedule(id1.execution_id)
        svc.transition(id1.execution_id, "RUNNING")
        svc.transition(id1.execution_id, "COMPLETED")

        # Different operation
        req2 = ExecutionRequest("appr-002", "ctr-002", "cap-002")
        id2 = svc.create_execution(
            req2, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        assert id2 is not None

    def test_non_idempotent_repeat_not_completed_allowed(self):
        """Re-creating a non-idempotent operation that hasn't Completed yet is OK."""
        svc = SchedulerService()
        svc.initialize()

        req = ExecutionRequest("appr-001", "ctr-001", "cap-001")
        id1 = svc.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        # id1 is CREATED, not COMPLETED — repeat should still be allowed
        # (only COMPLETED triggers the check)
        id2 = svc.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        assert id2 is not None
