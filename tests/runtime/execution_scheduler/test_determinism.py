"""Tests: Determinism — deterministic ordering + idempotency.

- Same inputs → same outputs
- Execution ordering is deterministic
- Idempotency decisions are reproducible
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
from src.sam.runtime.execution_scheduler.validation.ordering_validator import (
    OrderingValidator,
)
from src.sam.runtime.execution_scheduler.validation.idempotency_validator import (
    IdempotencyValidator,
)
from src.sam.runtime.contracts import ContractIdempotency


class TestDeterministicOrdering:
    def test_same_approval_order_same_sequence(self):
        """Given same approval order, execution sequence is identical."""
        def create_batch():
            svc = SchedulerService()
            svc.initialize()
            ids = []
            for i in range(5):
                req = ExecutionRequest(f"a{i}", f"c{i}", f"cp{i}")
                identity = svc.create_execution(req, approval_state="APPROVED")
                ids.append(identity)
            return [svc.get(eid.execution_id).sequence_number for eid in ids]

        batch1 = create_batch()
        batch2 = create_batch()
        assert batch1 == batch2 == [1, 2, 3, 4, 5]

    def test_get_next_sequence_deterministic(self):
        assert OrderingValidator.get_next_sequence([]) == 1
        assert OrderingValidator.get_next_sequence([]) == 1  # idempotent

    def test_sequence_monotonic(self):
        svc = SchedulerService()
        svc.initialize()
        sequences = []
        for i in range(10):
            req = ExecutionRequest(f"a{i}", f"c{i}", f"cp{i}")
            identity = svc.create_execution(req, approval_state="APPROVED")
            sequences.append(svc.get(identity.execution_id).sequence_number)
        # Must be strictly increasing
        for i in range(1, len(sequences)):
            assert sequences[i] == sequences[i-1] + 1


class TestDeterministicIdempotency:
    def test_same_idempotent_declaration_same_behavior(self):
        """IDEMPOTENT declaration always allows repeat."""
        svc = SchedulerService()
        svc.initialize()
        req = ExecutionRequest("a1", "c1", "cp1")

        id1 = svc.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.IDEMPOTENT.value,
        )
        svc.schedule(id1.execution_id)
        svc.transition(id1.execution_id, "RUNNING")
        svc.transition(id1.execution_id, "COMPLETED")

        # Repeat — deterministic: always allowed for IDEMPOTENT
        id2 = svc.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.IDEMPOTENT.value,
        )
        assert id2 is not None

    def test_same_non_idempotent_declaration_same_behavior(self):
        """NON_IDEMPOTENT declaration always blocks repeat."""
        svc1 = SchedulerService()
        svc1.initialize()
        req = ExecutionRequest("a1", "c1", "cp1")
        id1 = svc1.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        svc1.schedule(id1.execution_id)
        svc1.transition(id1.execution_id, "RUNNING")
        svc1.transition(id1.execution_id, "COMPLETED")

        with pytest.raises(Exception):
            svc1.create_execution(
                req, approval_state="APPROVED",
                contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
            )

        # Second scheduler, same setup — same outcome
        svc2 = SchedulerService()
        svc2.initialize()
        id2 = svc2.create_execution(
            req, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        svc2.schedule(id2.execution_id)
        svc2.transition(id2.execution_id, "RUNNING")
        svc2.transition(id2.execution_id, "COMPLETED")

        with pytest.raises(Exception):
            svc2.create_execution(
                req, approval_state="APPROVED",
                contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
            )

    def test_different_operations_independent(self):
        """Different operations don't interfere — deterministic isolation."""
        svc = SchedulerService()
        svc.initialize()

        # Operation A — non-idempotent, completed
        req_a = ExecutionRequest("appr-a", "ctr-a", "cap-a")
        id_a = svc.create_execution(
            req_a, approval_state="APPROVED",
            contract_idempotency=ContractIdempotency.NON_IDEMPOTENT.value,
        )
        svc.schedule(id_a.execution_id)
        svc.transition(id_a.execution_id, "RUNNING")
        svc.transition(id_a.execution_id, "COMPLETED")

        # Operation B — new, different — always allowed
        req_b = ExecutionRequest("appr-b", "ctr-b", "cap-b")
        id_b = svc.create_execution(req_b, approval_state="APPROVED")
        assert id_b is not None
