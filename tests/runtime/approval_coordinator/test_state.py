"""Tests: ApprovalState per-approval lifecycle state machine."""

import pytest

from src.sam.runtime.approval_coordinator.state.approval_state import (
    ApprovalState,
    ApprovalLifecycleState,
)
from src.sam.runtime.approval_coordinator.models.approval_identity import (
    ApprovalIdentity,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.contracts import ContractIdentity


@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity("c.id", "1.0.0", "cap.ref")


@pytest.fixture
def identity(contract_ref) -> ApprovalIdentity:
    return ApprovalIdentity(
        approval_id="test-state-001",
        decision_context="test",
        contract_reference=contract_ref,
        capability_reference="test.cap",
    )


@pytest.fixture
def appr_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="test",
        contract_reference=contract_ref,
        capability_reference="test.cap",
        requested_by="test",
    )


@pytest.fixture
def approval_state(identity, appr_request) -> ApprovalState:
    return ApprovalState(identity=identity, request=appr_request)


class TestApprovalLifecycleStateEnum:
    """Tests for ApprovalLifecycleState enum."""

    def test_has_seven_states(self):
        states = list(ApprovalLifecycleState)
        assert len(states) == 7

    def test_created_is_first(self):
        assert ApprovalLifecycleState.CREATED.value == "CREATED"

    def test_archived_is_last(self):
        assert ApprovalLifecycleState.ARCHIVED.value == "ARCHIVED"


class TestApprovalStateTransitions:
    """Tests for per-approval lifecycle transitions."""

    def test_initial_state_is_created(self, approval_state):
        assert approval_state.state == ApprovalLifecycleState.CREATED

    def test_created_to_pending(self, approval_state):
        assert approval_state.is_valid_transition(
            ApprovalLifecycleState.PENDING
        ) is True
        approval_state.transition(ApprovalLifecycleState.PENDING)
        assert approval_state.state == ApprovalLifecycleState.PENDING

    def test_created_to_rejected(self, approval_state):
        assert approval_state.is_valid_transition(
            ApprovalLifecycleState.REJECTED
        ) is True
        approval_state.transition(ApprovalLifecycleState.REJECTED)
        assert approval_state.state == ApprovalLifecycleState.REJECTED

    def test_pending_to_approved(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        assert approval_state.is_valid_transition(
            ApprovalLifecycleState.APPROVED
        ) is True
        approval_state.transition(ApprovalLifecycleState.APPROVED)
        assert approval_state.state == ApprovalLifecycleState.APPROVED

    def test_pending_to_rejected(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.REJECTED)
        assert approval_state.state == ApprovalLifecycleState.REJECTED

    def test_pending_to_expired(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.EXPIRED)
        assert approval_state.state == ApprovalLifecycleState.EXPIRED

    def test_pending_to_cancelled(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.CANCELLED)
        assert approval_state.state == ApprovalLifecycleState.CANCELLED

    def test_approved_to_expired(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.APPROVED)
        approval_state.transition(ApprovalLifecycleState.EXPIRED)
        assert approval_state.state == ApprovalLifecycleState.EXPIRED

    def test_approved_to_archived(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.APPROVED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)
        assert approval_state.state == ApprovalLifecycleState.ARCHIVED

    def test_rejected_to_archived(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.REJECTED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)
        assert approval_state.state == ApprovalLifecycleState.ARCHIVED

    def test_expired_to_archived(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.EXPIRED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)
        assert approval_state.state == ApprovalLifecycleState.ARCHIVED

    def test_cancelled_to_archived(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.CANCELLED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)
        assert approval_state.state == ApprovalLifecycleState.ARCHIVED

    def test_invalid_created_to_approved(self, approval_state):
        """Cannot skip PENDING — CREATED → APPROVED is illegal."""
        assert approval_state.is_valid_transition(
            ApprovalLifecycleState.APPROVED
        ) is False
        with pytest.raises(ValueError, match="Invalid approval transition"):
            approval_state.transition(ApprovalLifecycleState.APPROVED)

    def test_invalid_created_to_archived(self, approval_state):
        assert approval_state.is_valid_transition(
            ApprovalLifecycleState.ARCHIVED
        ) is False

    def test_from_archived_is_invalid(self, approval_state):
        """ARCHIVED is terminal — no outgoing transitions."""
        # Get to ARCHIVED via PENDING → REJECTED → ARCHIVED
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.REJECTED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)

        with pytest.raises(ValueError):
            approval_state.transition(ApprovalLifecycleState.APPROVED)

    def test_archived_is_terminal(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.PENDING)
        approval_state.transition(ApprovalLifecycleState.APPROVED)
        approval_state.transition(ApprovalLifecycleState.ARCHIVED)
        assert approval_state.is_terminal() is True

    def test_created_is_not_terminal(self, approval_state):
        assert approval_state.is_terminal() is False

    def test_same_state_is_noop(self, approval_state):
        approval_state.transition(ApprovalLifecycleState.CREATED)
        assert approval_state.state == ApprovalLifecycleState.CREATED

    def test_identity_access(self, approval_state, identity):
        assert approval_state.identity == identity

    def test_request_access(self, approval_state, appr_request):
        assert approval_state.request == appr_request

    def test_set_and_get_decision(self, approval_state):
        from src.sam.runtime.approval_coordinator.models.approval_decision import (
            ApprovalDecision,
        )

        assert approval_state.has_decision() is False
        decision = ApprovalDecision.approved("test-id", "ok")
        approval_state.set_decision(decision)
        assert approval_state.has_decision() is True
        assert approval_state.decision == decision

    def test_to_dict(self, approval_state):
        d = approval_state.to_dict()
        assert d["approval_id"] == "test-state-001"
        assert d["state"] == "CREATED"
        assert d["capability_reference"] == "test.cap"
        assert d["has_decision"] is False

    def test_to_dict_with_decision(self, approval_state):
        from src.sam.runtime.approval_coordinator.models.approval_decision import (
            ApprovalDecision,
        )

        decision = ApprovalDecision.approved("test-id", "reasoning here")
        approval_state.set_decision(decision)
        d = approval_state.to_dict()
        assert d["has_decision"] is True
        assert d["decision_state"] == "APPROVED"
        assert d["decision_reason"] == "reasoning here"

    def test_repr(self, approval_state):
        r = repr(approval_state)
        assert "test-state-001" in r
        assert "CREATED" in r
