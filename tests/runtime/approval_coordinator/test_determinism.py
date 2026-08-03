"""Tests: Approval determinism — same input, same output."""

import pytest

from src.sam.runtime.contracts import ContractIdentity
from src.sam.runtime.approval_coordinator.services.coordinator_service import (
    ApprovalCoordinator,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecisionState,
)


@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity("test.c", "1.0.0", "test.cap")


@pytest.fixture
def appr_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="determinism test",
        contract_reference=contract_ref,
        capability_reference="test.cap",
        requested_by="test",
    )


class TestDeterminism:
    """Tests for deterministic evaluation output."""

    def test_same_policy_same_decision(self, appr_request):
        def policy(req):
            return ApprovalDecisionState.APPROVED

        c1 = ApprovalCoordinator()
        c1.initialize()
        i1 = c1.create_approval(appr_request)
        d1 = c1.evaluate(i1.approval_id, policy)

        c2 = ApprovalCoordinator()
        c2.initialize()
        i2 = c2.create_approval(appr_request)
        d2 = c2.evaluate(i2.approval_id, policy)

        assert d1.state == d2.state

    def test_different_policy_different_decision(self, appr_request):
        def approve_policy(req):
            return ApprovalDecisionState.APPROVED

        def reject_policy(req):
            return ApprovalDecisionState.REJECTED

        c = ApprovalCoordinator()
        c.initialize()

        i1 = c.create_approval(appr_request)
        d1 = c.evaluate(i1.approval_id, approve_policy)
        assert d1.state == ApprovalDecisionState.APPROVED

        i2 = c.create_approval(appr_request)
        d2 = c.evaluate(i2.approval_id, reject_policy)
        assert d2.state == ApprovalDecisionState.REJECTED

    def test_repeated_evaluation_same_decision(self, appr_request):
        """Same approval evaluated twice with same policy = same decision."""
        def policy(req):
            return ApprovalDecisionState.APPROVED

        c = ApprovalCoordinator()
        c.initialize()
        identity = c.create_approval(appr_request)

        d1 = c.evaluate(identity.approval_id, policy)
        assert d1.state == ApprovalDecisionState.APPROVED

    def test_different_requests_independent(self, appr_request, contract_ref):
        """Different requests evaluated independently with same policy."""
        def policy(req):
            return ApprovalDecisionState.APPROVED

        req2 = ApprovalRequest(
            decision_context="other context",
            contract_reference=contract_ref,
            capability_reference="other.cap",
            requested_by="test",
        )

        c = ApprovalCoordinator()
        c.initialize()

        i1 = c.create_approval(appr_request)
        i2 = c.create_approval(req2)

        assert i1.approval_id != i2.approval_id

        d1 = c.evaluate(i1.approval_id, policy)
        d2 = c.evaluate(i2.approval_id, policy)

        assert d1.state == ApprovalDecisionState.APPROVED
        assert d2.state == ApprovalDecisionState.APPROVED
