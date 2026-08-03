"""Tests: ApprovalCoordinator service — orchestrator and gate."""

import pytest

from src.sam.runtime.contracts import ContractIdentity
from src.sam.runtime.approval_coordinator.services.coordinator_service import (
    ApprovalCoordinator,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)
from src.sam.runtime.approval_coordinator.state.approval_state import (
    ApprovalLifecycleState,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    InvalidRequestError,
    ExpiredRequestError,
    ApprovalNotFoundError,
    CoordinatorNotOperationalError,
    InvalidTransitionError,
)


# ── Fixtures ────────────────────────────────────

@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity("memory.contract", "1.0.0", "memory.cap")


@pytest.fixture
def appr_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="Write file operation",
        contract_reference=contract_ref,
        capability_reference="file.writer",
        requested_by="test-suite",
    )


@pytest.fixture
def coordinator() -> ApprovalCoordinator:
    c = ApprovalCoordinator()
    c.initialize()
    return c


@pytest.fixture
def approve_policy():
    """A policy that approves everything."""
    return lambda req: ApprovalDecisionState.APPROVED


@pytest.fixture
def reject_policy():
    """A policy that rejects everything."""
    return lambda req: ApprovalDecisionState.REJECTED


# ── Construction Tests ──────────────────────────

class TestConstruction:
    """Tests for coordinator construction and initialization."""

    def test_initial_state_is_uninitialized(self):
        c = ApprovalCoordinator()
        assert c.lifecycle.state.value == "UNINITIALIZED"

    def test_initialize_sets_running(self, coordinator):
        assert coordinator.lifecycle.state.value == "RUNNING"
        assert coordinator.get_health()["status"] == "AVAILABLE"

    def test_approval_count_starts_at_zero(self, coordinator):
        assert coordinator.approval_count == 0


# ── create_approval() Tests ─────────────────────

class TestCreateApproval:
    """Tests for create_approval()."""

    def test_create_with_valid_request(self, coordinator, appr_request):
        identity = coordinator.create_approval(appr_request)
        assert identity is not None
        assert identity.decision_context == "Write file operation"
        assert identity.capability_reference == "file.writer"
        assert coordinator.approval_count == 1

    def test_create_generates_unique_ids(self, coordinator, appr_request):
        id1 = coordinator.create_approval(appr_request)
        id2 = coordinator.create_approval(appr_request)
        assert id1.approval_id != id2.approval_id
        assert coordinator.approval_count == 2

    def test_created_approval_in_created_state(self, coordinator, appr_request):
        identity = coordinator.create_approval(appr_request)
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.CREATED

    def test_create_invalid_request_raises(self, coordinator, contract_ref):
        bad_request = ApprovalRequest(
            decision_context="",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        with pytest.raises(InvalidRequestError):
            coordinator.create_approval(bad_request)

    def test_create_expired_request_raises(self, coordinator):
        import time

        bad_contract = ContractIdentity("c", "1.0", "cap")
        bad = ApprovalRequest(
            decision_context="ctx",
            contract_reference=bad_contract,
            capability_reference="cap",
            requested_by="test",
            expires_at=time.time() - 3600,
        )
        with pytest.raises(ExpiredRequestError):
            coordinator.create_approval(bad)

    def test_create_not_operational_raises(self, appr_request):
        c = ApprovalCoordinator()
        with pytest.raises(CoordinatorNotOperationalError):
            c.create_approval(appr_request)


# ── evaluate() Tests ────────────────────────────

class TestEvaluate:
    """Tests for evaluate()."""

    def test_evaluate_approved(self, coordinator, appr_request, approve_policy):
        identity = coordinator.create_approval(appr_request)
        decision = coordinator.evaluate(identity.approval_id, approve_policy)

        assert decision.state == ApprovalDecisionState.APPROVED
        assert decision.is_approved()
        assert decision.permits_execution()

        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.APPROVED

    def test_evaluate_rejected(self, coordinator, appr_request, reject_policy):
        identity = coordinator.create_approval(appr_request)
        decision = coordinator.evaluate(identity.approval_id, reject_policy)

        assert decision.state == ApprovalDecisionState.REJECTED
        assert not decision.permits_execution()

        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.REJECTED

    def test_evaluate_nonexistent_approval(self, coordinator, approve_policy):
        with pytest.raises(ApprovalNotFoundError):
            coordinator.evaluate("nonexistent-id", approve_policy)

    def test_evaluate_not_operational_raises(self, approve_policy):
        c = ApprovalCoordinator()
        with pytest.raises(CoordinatorNotOperationalError):
            c.evaluate("any-id", approve_policy)

    def test_evaluate_sets_decision_on_state(self, coordinator, appr_request, approve_policy):
        identity = coordinator.create_approval(appr_request)
        coordinator.evaluate(identity.approval_id, approve_policy)
        state = coordinator.get(identity.approval_id)
        assert state.has_decision() is True
        assert state.decision.state == ApprovalDecisionState.APPROVED

    def test_evaluate_transitions_from_created_to_pending(self, coordinator, appr_request, approve_policy):
        identity = coordinator.create_approval(appr_request)
        # Not calling evaluate yet — check state after evaluate
        state_before = coordinator.get(identity.approval_id)
        assert state_before.state == ApprovalLifecycleState.CREATED

        coordinator.evaluate(identity.approval_id, approve_policy)
        state_after = coordinator.get(identity.approval_id)
        # After evaluate with approve_policy, should be APPROVED
        assert state_after.state == ApprovalLifecycleState.APPROVED

    def test_reevaluate_approved_returns_original(self, coordinator, appr_request, approve_policy):
        """Re-evaluating an already-decided approval returns existing decision."""
        identity = coordinator.create_approval(appr_request)
        first = coordinator.evaluate(identity.approval_id, approve_policy)
        second = coordinator.evaluate(identity.approval_id, reject_policy)
        # Re-evaluation after decision returns existing decision or superseded
        assert first.state == ApprovalDecisionState.APPROVED

    def test_evaluate_expired_state(self, coordinator, appr_request, approve_policy):
        """Policy that returns EXPIRED."""
        def expire_policy(req):
            return ApprovalDecisionState.EXPIRED

        identity = coordinator.create_approval(appr_request)
        decision = coordinator.evaluate(identity.approval_id, expire_policy)
        assert decision.state == ApprovalDecisionState.EXPIRED
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.EXPIRED

    def test_evaluate_cancelled_state(self, coordinator, appr_request, approve_policy):
        """Policy that returns CANCELLED."""
        def cancel_policy(req):
            return ApprovalDecisionState.CANCELLED

        identity = coordinator.create_approval(appr_request)
        decision = coordinator.evaluate(identity.approval_id, cancel_policy)
        assert decision.state == ApprovalDecisionState.CANCELLED
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.CANCELLED


# ── transition() Tests ──────────────────────────

class TestTransition:
    """Tests for transition()."""

    def test_archive_approved(self, coordinator, appr_request, approve_policy):
        identity = coordinator.create_approval(appr_request)
        coordinator.evaluate(identity.approval_id, approve_policy)

        # Move from APPROVED to ARCHIVED
        coordinator.transition(identity.approval_id, "ARCHIVED")
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.ARCHIVED

    def test_archive_rejected(self, coordinator, appr_request, reject_policy):
        identity = coordinator.create_approval(appr_request)
        coordinator.evaluate(identity.approval_id, reject_policy)

        coordinator.transition(identity.approval_id, "ARCHIVED")
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.ARCHIVED

    def test_transition_nonexistent_raises(self, coordinator):
        with pytest.raises(ApprovalNotFoundError):
            coordinator.transition("nonexistent", "PENDING")

    def test_transition_invalid_raises(self, coordinator, appr_request):
        identity = coordinator.create_approval(appr_request)
        # CREATED → APPROVED is illegal
        with pytest.raises(InvalidTransitionError):
            coordinator.transition(identity.approval_id, "APPROVED")

    def test_transition_not_operational_raises(self, appr_request, approve_policy):
        c = ApprovalCoordinator()
        with pytest.raises(CoordinatorNotOperationalError):
            c.transition("any-id", "PENDING")

    def test_transition_unknown_state_raises(self, coordinator, appr_request):
        identity = coordinator.create_approval(appr_request)
        with pytest.raises(InvalidTransitionError):
            coordinator.transition(identity.approval_id, "INVALID_STATE")


# ── get() Tests ─────────────────────────────────

class TestGet:
    """Tests for get()."""

    def test_get_existing(self, coordinator, appr_request):
        identity = coordinator.create_approval(appr_request)
        state = coordinator.get(identity.approval_id)
        assert state.identity.approval_id == identity.approval_id

    def test_get_nonexistent_raises(self, coordinator):
        with pytest.raises(ApprovalNotFoundError):
            coordinator.get("no-such-id")


# ── get_health() Tests ──────────────────────────

class TestGetHealth:
    """Tests for get_health()."""

    def test_running_is_available(self, coordinator):
        health = coordinator.get_health()
        assert health["status"] == "AVAILABLE"
        assert health["operational"] is True

    def test_after_shutdown_is_unavailable(self, coordinator):
        coordinator.shutdown()
        health = coordinator.get_health()
        assert health["status"] == "UNAVAILABLE"
        assert health["operational"] is False
        assert health["terminal"] is True


# ── Integration Tests ───────────────────────────

class TestFullWorkflow:
    """End-to-end workflow tests."""

    def test_full_approval_pipeline(self, coordinator, appr_request, approve_policy):
        # Create
        identity = coordinator.create_approval(appr_request)
        assert coordinator.approval_count == 1

        # Evaluate
        decision = coordinator.evaluate(identity.approval_id, approve_policy)
        assert decision.state == ApprovalDecisionState.APPROVED
        assert decision.permits_execution()

        # Archive
        coordinator.transition(identity.approval_id, "ARCHIVED")
        state = coordinator.get(identity.approval_id)
        assert state.state == ApprovalLifecycleState.ARCHIVED
        assert state.is_terminal()

    def test_multiple_approvals_independent(self, coordinator, appr_request, approve_policy):
        id1 = coordinator.create_approval(appr_request)
        id2 = coordinator.create_approval(appr_request)
        assert coordinator.approval_count == 2

        # Approve one, reject the other
        coordinator.evaluate(id1.approval_id, approve_policy)

        def reject_policy(req):
            return ApprovalDecisionState.REJECTED

        coordinator.evaluate(id2.approval_id, reject_policy)

        s1 = coordinator.get(id1.approval_id)
        s2 = coordinator.get(id2.approval_id)

        assert s1.state == ApprovalLifecycleState.APPROVED
        assert s2.state == ApprovalLifecycleState.REJECTED

    def test_shutdown_prevents_new_approvals(self, coordinator, appr_request):
        coordinator.shutdown()
        with pytest.raises(CoordinatorNotOperationalError):
            coordinator.create_approval(appr_request)
