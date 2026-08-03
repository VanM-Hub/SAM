"""Tests: Boundary enforcement — no bypass, public API only."""

import pytest

from src.sam.runtime.contracts import ContractIdentity
from src.sam.runtime.approval_coordinator.services.coordinator_service import (
    ApprovalCoordinator,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.validation.boundary_validator import (
    BoundaryValidator,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    CoordinatorNotOperationalError,
)


@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity("b.c", "1.0.0", "b.cap")


@pytest.fixture
def appr_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="boundary test",
        contract_reference=contract_ref,
        capability_reference="boundary.cap",
        requested_by="test",
    )


class TestBoundary:
    """Tests for boundary enforcement."""

    def test_all_public_api_methods_authorized(self):
        methods = ["create_approval", "evaluate", "transition", "get", "get_health"]
        for method in methods:
            assert BoundaryValidator.is_authorized(method) is True

    def test_internal_accessor_not_authorized(self):
        assert BoundaryValidator.is_authorized("_ensure_approval") is False
        assert BoundaryValidator.is_authorized("_require_operational") is False
        assert BoundaryValidator.is_authorized("_approvals") is False

    def test_create_approval_is_authorized_entry(self, appr_request):
        c = ApprovalCoordinator()
        c.initialize()
        # create_approval works through public API
        identity = c.create_approval(appr_request)
        assert identity is not None

    def test_evaluate_is_authorized_entry(self, appr_request):
        c = ApprovalCoordinator()
        c.initialize()
        identity = c.create_approval(appr_request)

        from src.sam.runtime.approval_coordinator.models.approval_decision import (
            ApprovalDecisionState,
        )

        def policy(req):
            return ApprovalDecisionState.APPROVED

        decision = c.evaluate(identity.approval_id, policy)
        assert decision.state == ApprovalDecisionState.APPROVED

    def test_transition_is_authorized_entry(self, appr_request):
        c = ApprovalCoordinator()
        c.initialize()
        identity = c.create_approval(appr_request)
        c.transition(identity.approval_id, "PENDING")
        state = c.get(identity.approval_id)
        assert state.state.value == "PENDING"

    def test_get_is_authorized_entry(self, appr_request):
        c = ApprovalCoordinator()
        c.initialize()
        identity = c.create_approval(appr_request)
        state = c.get(identity.approval_id)
        assert state.identity.approval_id == identity.approval_id

    def test_get_health_is_authorized_entry(self):
        c = ApprovalCoordinator()
        health = c.get_health()
        assert "status" in health

    def test_no_direct_execution_possible(self, appr_request):
        """The Approval Coordinator must not have any execution path."""
        c = ApprovalCoordinator()
        c.initialize()

        # verify no 'execute' or 'run' public method exists
        forbidden = ["execute", "run", "perform", "audit", "resolve", "discover"]
        for method in forbidden:
            assert not hasattr(c, method) or method not in dir(type(c)), (
                f"ApprovalCoordinator has forbidden method: {method}"
            )

    def test_not_operational_blocks_all_operations(self, appr_request):
        c = ApprovalCoordinator()
        # Not initialized

        from src.sam.runtime.approval_coordinator.models.approval_decision import (
            ApprovalDecisionState,
        )

        def policy(req):
            return ApprovalDecisionState.APPROVED

        with pytest.raises(CoordinatorNotOperationalError):
            c.create_approval(appr_request)
        with pytest.raises(CoordinatorNotOperationalError):
            c.evaluate("any-id", policy)
        with pytest.raises(CoordinatorNotOperationalError):
            c.transition("any-id", "PENDING")
