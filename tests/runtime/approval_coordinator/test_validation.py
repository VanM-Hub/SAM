"""Tests: Approval Coordinator validators."""

import time
import pytest

from src.sam.runtime.contracts import ContractIdentity
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)
from src.sam.runtime.approval_coordinator.validation.request_validator import (
    RequestValidator,
)
from src.sam.runtime.approval_coordinator.validation.decision_validator import (
    DecisionValidator,
)
from src.sam.runtime.approval_coordinator.validation.lifecycle_validator import (
    LifecycleValidator,
)
from src.sam.runtime.approval_coordinator.validation.boundary_validator import (
    BoundaryValidator,
)
from src.sam.runtime.approval_coordinator.state.approval_state import (
    ApprovalLifecycleState,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    InvalidRequestError,
    ExpiredRequestError,
    InvalidTransitionError,
)


@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity("c.id", "1.0.0", "cap.ref")


@pytest.fixture
def valid_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="valid context",
        contract_reference=contract_ref,
        capability_reference="test.cap",
        requested_by="validator-test",
    )


# ── RequestValidator Tests ──────────────────────

class TestRequestValidator:
    """Tests for RequestValidator."""

    def test_valid_request(self, valid_request):
        assert RequestValidator.validate(valid_request) is True

    def test_empty_decision_context(self, contract_ref):
        request = ApprovalRequest(
            decision_context="",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        with pytest.raises(InvalidRequestError):
            RequestValidator.validate(request)

    def test_empty_capability_reference(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="",
            requested_by="test",
        )
        with pytest.raises(InvalidRequestError):
            RequestValidator.validate(request)

    def test_empty_requested_by(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="",
        )
        with pytest.raises(InvalidRequestError):
            RequestValidator.validate(request)

    def test_invalid_contract_reference(self):
        from src.sam.runtime.contracts import ContractIdentity

        bad_contract = ContractIdentity("", "", "")
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=bad_contract,
            capability_reference="cap",
            requested_by="test",
        )
        with pytest.raises(InvalidRequestError):
            RequestValidator.validate(request)

    def test_expired_request(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
            expires_at=time.time() - 3600,
        )
        with pytest.raises(ExpiredRequestError):
            RequestValidator.validate(request)

    def test_is_valid_returns_false_for_invalid(self, contract_ref):
        request = ApprovalRequest(
            decision_context="",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        assert RequestValidator.is_valid(request) is False

    def test_is_valid_returns_true(self, valid_request):
        assert RequestValidator.is_valid(valid_request) is True


# ── DecisionValidator Tests ─────────────────────

class TestDecisionValidator:
    """Tests for DecisionValidator."""

    def test_valid_decision(self):
        d = ApprovalDecision.approved("id", "valid reason")
        assert DecisionValidator.validate(d) is True

    def test_empty_reason(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="",
            approval_id="id",
            decided_at=time.time(),
            decided_by="system",
        )
        with pytest.raises(InvalidRequestError):
            DecisionValidator.validate(d)

    def test_empty_approval_id(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="reason",
            approval_id="",
            decided_at=time.time(),
            decided_by="system",
        )
        with pytest.raises(InvalidRequestError):
            DecisionValidator.validate(d)

    def test_empty_decided_by(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="reason",
            approval_id="id",
            decided_at=time.time(),
            decided_by="",
        )
        with pytest.raises(InvalidRequestError):
            DecisionValidator.validate(d)

    def test_is_valid_returns_false(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="",
            approval_id="id",
            decided_at=time.time(),
            decided_by="system",
        )
        assert DecisionValidator.is_valid(d) is False

    def test_is_valid_returns_true(self):
        d = ApprovalDecision.approved("id", "ok")
        assert DecisionValidator.is_valid(d) is True


# ── LifecycleValidator Tests ────────────────────

class TestLifecycleValidator:
    """Tests for LifecycleValidator."""

    def test_valid_transitions(self):
        valid_pairs = [
            (ApprovalLifecycleState.CREATED, ApprovalLifecycleState.PENDING),
            (ApprovalLifecycleState.CREATED, ApprovalLifecycleState.REJECTED),
            (ApprovalLifecycleState.PENDING, ApprovalLifecycleState.APPROVED),
            (ApprovalLifecycleState.PENDING, ApprovalLifecycleState.REJECTED),
            (ApprovalLifecycleState.PENDING, ApprovalLifecycleState.EXPIRED),
            (ApprovalLifecycleState.PENDING, ApprovalLifecycleState.CANCELLED),
            (ApprovalLifecycleState.APPROVED, ApprovalLifecycleState.EXPIRED),
            (ApprovalLifecycleState.APPROVED, ApprovalLifecycleState.ARCHIVED),
            (ApprovalLifecycleState.REJECTED, ApprovalLifecycleState.ARCHIVED),
            (ApprovalLifecycleState.EXPIRED, ApprovalLifecycleState.ARCHIVED),
            (ApprovalLifecycleState.CANCELLED, ApprovalLifecycleState.ARCHIVED),
        ]
        for current, target in valid_pairs:
            assert LifecycleValidator.validate_transition(current, target) is True

    def test_invalid_transitions(self):
        invalid_pairs = [
            (ApprovalLifecycleState.CREATED, ApprovalLifecycleState.APPROVED),
            (ApprovalLifecycleState.CREATED, ApprovalLifecycleState.ARCHIVED),
            (ApprovalLifecycleState.ARCHIVED, ApprovalLifecycleState.PENDING),
            (ApprovalLifecycleState.APPROVED, ApprovalLifecycleState.REJECTED),
            (ApprovalLifecycleState.REJECTED, ApprovalLifecycleState.APPROVED),
        ]
        for current, target in invalid_pairs:
            assert LifecycleValidator.is_valid(current, target) is False

    def test_from_archived_is_invalid(self):
        assert LifecycleValidator.is_valid(
            ApprovalLifecycleState.ARCHIVED,
            ApprovalLifecycleState.PENDING,
        ) is False

    def test_same_state_is_noop(self):
        for state in ApprovalLifecycleState:
            assert LifecycleValidator.validate_transition(state, state) is True

    def test_raises_on_invalid(self):
        with pytest.raises(InvalidTransitionError):
            LifecycleValidator.validate_transition(
                ApprovalLifecycleState.CREATED,
                ApprovalLifecycleState.APPROVED,
            )


# ── BoundaryValidator Tests ─────────────────────

class TestBoundaryValidator:
    """Tests for BoundaryValidator."""

    def test_authorized_methods(self):
        authorized = [
            "create_approval",
            "evaluate",
            "transition",
            "get",
            "get_health",
        ]
        for method in authorized:
            assert BoundaryValidator.validate_entry_point(method) is True

    def test_unauthorized_method_raises(self):
        with pytest.raises(ValueError):
            BoundaryValidator.validate_entry_point("execute_operation")

    def test_unauthorized_method_returns_false(self):
        assert BoundaryValidator.is_authorized("internal_helper") is False

    def test_get_authorized_entry_points(self):
        points = BoundaryValidator.get_authorized_entry_points()
        assert len(points) == 5
        assert "create_approval" in points
        assert "evaluate" in points
        assert "transition" in points
        assert "get" in points
        assert "get_health" in points
