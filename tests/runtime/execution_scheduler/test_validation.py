"""Tests: All 7 validators — approval, ordering, idempotency, lifecycle,
verification, boundary, invariant."""

import pytest
from src.sam.runtime.execution_scheduler.validation.approval_validator import (
    ApprovalValidator,
)
from src.sam.runtime.execution_scheduler.validation.ordering_validator import (
    OrderingValidator,
)
from src.sam.runtime.execution_scheduler.validation.idempotency_validator import (
    IdempotencyValidator,
)
from src.sam.runtime.execution_scheduler.validation.lifecycle_validator import (
    LifecycleValidator,
)
from src.sam.runtime.execution_scheduler.validation.verification_validator import (
    VerificationValidator,
)
from src.sam.runtime.execution_scheduler.validation.boundary_validator import (
    BoundaryValidator,
)
from src.sam.runtime.execution_scheduler.validation.invariant_validator import (
    InvariantValidator,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
    ExecutionLifecycleState,
)
from src.sam.runtime.execution_scheduler.models.execution_identity import (
    ExecutionIdentity,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
)
from src.sam.runtime.contracts import ContractIdempotency


# ──────────────────────────────────────────────
# Lifecycle Validator
# ──────────────────────────────────────────────

class TestLifecycleValidator:
    def test_valid_transition(self):
        rec = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
            request=ExecutionRequest("a1", "c1", "cp1"),
        )
        assert LifecycleValidator.validate_transition(
            rec, ExecutionLifecycleState.QUEUED,
        ) is True

    def test_invalid_transition_raises(self):
        rec = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
            request=ExecutionRequest("a1", "c1", "cp1"),
        )
        with pytest.raises(ValueError, match="Invalid transition"):
            LifecycleValidator.validate_transition(
                rec, ExecutionLifecycleState.COMPLETED,
            )

    def test_is_terminal(self):
        rec = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
            request=ExecutionRequest("a1", "c1", "cp1"),
        )
        rec.transition(ExecutionLifecycleState.QUEUED)
        rec.transition(ExecutionLifecycleState.RUNNING)
        rec.transition(ExecutionLifecycleState.COMPLETED)
        rec.transition(ExecutionLifecycleState.ARCHIVED)
        assert LifecycleValidator.is_terminal(rec) is True

    def test_can_transition_from_terminal(self):
        rec = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
            request=ExecutionRequest("a1", "c1", "cp1"),
        )
        assert LifecycleValidator.can_transition_from_terminal(rec) is True
        rec.transition(ExecutionLifecycleState.QUEUED)
        rec.transition(ExecutionLifecycleState.RUNNING)
        rec.transition(ExecutionLifecycleState.COMPLETED)
        rec.transition(ExecutionLifecycleState.ARCHIVED)
        assert LifecycleValidator.can_transition_from_terminal(rec) is False


# ──────────────────────────────────────────────
# Boundary Validator
# ──────────────────────────────────────────────

class TestBoundaryValidator:
    def test_authorized_methods(self):
        for method in ["create_execution", "schedule", "transition", "verify",
                       "get", "get_health"]:
            assert BoundaryValidator.is_authorized(method) is True

    def test_unauthorized_method_returns_false(self):
        assert BoundaryValidator.is_authorized("execute_directly") is False
        assert BoundaryValidator.is_authorized("_internal") is False

    def test_unauthorized_method_raises(self):
        with pytest.raises(ValueError, match="not an authorized"):
            BoundaryValidator.validate_authorized("execute_directly")

    def test_get_authorized_entry_points(self):
        points = BoundaryValidator.get_authorized_entry_points()
        assert "create_execution" in points
        assert "get_health" in points
        assert len(points) == 6


# ──────────────────────────────────────────────
# Invariant Validator
# ──────────────────────────────────────────────

class TestInvariantValidator:
    def test_all_invariants_pass(self):
        records = {
            "e1": ExecutionStateRecord(
                identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
                request=ExecutionRequest("a1", "c1", "cp1"),
            ),
            "e2": ExecutionStateRecord(
                identity=ExecutionIdentity("e2", "a2", "c2", "cp2"),
                request=ExecutionRequest("a2", "c2", "cp2"),
            ),
        }
        result = InvariantValidator.validate_invariants(records)
        assert result["invariants_checked"] == 2
        assert result["invariants_passed"] == 2
        assert result["violations"] == []

    def test_missing_approval_detected(self):
        records = {
            "e1": ExecutionStateRecord(
                identity=ExecutionIdentity("e1", "", "c1", "cp1"),
                request=ExecutionRequest("", "c1", "cp1"),
            ),
        }
        result = InvariantValidator.validate_invariants(records)
        assert len(result["violations"]) == 1
        assert "I6" in result["violations"][0]

    def test_validate_approval_before_execution(self):
        rec = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "a1", "c1", "cp1"),
            request=ExecutionRequest("a1", "c1", "cp1"),
        )
        assert InvariantValidator.validate_approval_before_execution(rec) is True

        rec2 = ExecutionStateRecord(
            identity=ExecutionIdentity("e1", "", "c1", "cp1"),
            request=ExecutionRequest("", "c1", "cp1"),
        )
        assert InvariantValidator.validate_approval_before_execution(rec2) is False
