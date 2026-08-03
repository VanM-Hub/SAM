"""Tests: ApprovalIdentity, ApprovalRequest, and ApprovalDecision models."""

import time
import pytest

from src.sam.runtime.approval_coordinator.models.approval_identity import (
    ApprovalIdentity,
)
from src.sam.runtime.approval_coordinator.models.approval_request import (
    ApprovalRequest,
)
from src.sam.runtime.approval_coordinator.models.approval_decision import (
    ApprovalDecision,
    ApprovalDecisionState,
)
from src.sam.runtime.contracts import ContractIdentity


# ── Fixtures ────────────────────────────────────

@pytest.fixture
def contract_ref() -> ContractIdentity:
    return ContractIdentity(
        contract_id="memory.contract",
        version="1.0.0",
        capability_reference="memory.capability",
    )


@pytest.fixture
def approval_request(contract_ref) -> ApprovalRequest:
    return ApprovalRequest(
        decision_context="Test approval context",
        contract_reference=contract_ref,
        capability_reference="memory.capability",
        requested_by="test-suite",
    )


@pytest.fixture
def approval_identity(contract_ref) -> ApprovalIdentity:
    return ApprovalIdentity(
        approval_id="test-001",
        decision_context="Test context",
        contract_reference=contract_ref,
        capability_reference="memory.capability",
    )


# ── ApprovalIdentity Tests ──────────────────────

class TestApprovalIdentity:
    """Tests for ApprovalIdentity model."""

    def test_create_with_required_fields(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="approval-1",
            decision_context="write-file-operation",
            contract_reference=contract_ref,
            capability_reference="file.writer",
        )
        assert identity.approval_id == "approval-1"
        assert identity.decision_context == "write-file-operation"
        assert identity.capability_reference == "file.writer"
        assert identity.contract_reference == contract_ref

    def test_create_with_all_fields(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="approval-2",
            decision_context="read-file",
            contract_reference=contract_ref,
            capability_reference="file.reader",
            citizen_reference="citizen-42",
        )
        assert identity.citizen_reference == "citizen-42"

    def test_default_citizen_reference_is_none(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="a-1",
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
        )
        assert identity.citizen_reference is None

    def test_validate_with_valid_fields(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="a-1",
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
        )
        assert identity.validate() is True

    def test_validate_with_empty_approval_id(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="",
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
        )
        assert identity.validate() is False

    def test_validate_with_empty_context(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="a-1",
            decision_context="",
            contract_reference=contract_ref,
            capability_reference="cap",
        )
        assert identity.validate() is False

    def test_validate_with_empty_capability(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="a-1",
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="",
        )
        assert identity.validate() is False

    def test_identity_is_frozen(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="a-1",
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
        )
        with pytest.raises(Exception):
            identity.approval_id = "new-id"  # type: ignore

    def test_repr_contains_key_info(self, contract_ref):
        identity = ApprovalIdentity(
            approval_id="approval-99",
            decision_context="critical operation",
            contract_reference=contract_ref,
            capability_reference="danger.zone",
        )
        r = repr(identity)
        assert "approval-99" in r
        assert "danger.zone" in r


# ── ApprovalRequest Tests ───────────────────────

class TestApprovalRequest:
    """Tests for ApprovalRequest model."""

    def test_create_with_required_fields(self, contract_ref):
        request = ApprovalRequest(
            decision_context="write-file",
            contract_reference=contract_ref,
            capability_reference="file.writer",
            requested_by="unit-test",
        )
        assert request.decision_context == "write-file"
        assert request.capability_reference == "file.writer"
        assert request.requested_by == "unit-test"

    def test_create_with_optional_fields(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
            citizen_reference="citizen-1",
            expires_at=time.time() + 3600,
        )
        assert request.citizen_reference == "citizen-1"
        assert request.expires_at is not None

    def test_default_expires_at_is_none(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        assert request.expires_at is None

    def test_validate_valid_request(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        assert request.validate() is True

    def test_validate_empty_context(self, contract_ref):
        request = ApprovalRequest(
            decision_context="",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        assert request.validate() is False

    def test_validate_empty_capability(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="",
            requested_by="test",
        )
        assert request.validate() is False

    def test_validate_empty_requested_by(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="",
        )
        assert request.validate() is False

    def test_is_expired_none_expiry(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        assert request.is_expired() is False

    def test_is_expired_past(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
            expires_at=time.time() - 3600,
        )
        assert request.is_expired() is True

    def test_is_expired_future(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
            expires_at=time.time() + 86400,
        )
        assert request.is_expired() is False

    def test_request_is_frozen(self, contract_ref):
        request = ApprovalRequest(
            decision_context="ctx",
            contract_reference=contract_ref,
            capability_reference="cap",
            requested_by="test",
        )
        with pytest.raises(Exception):
            request.decision_context = "changed"  # type: ignore

    def test_repr_contains_key_info(self, contract_ref):
        request = ApprovalRequest(
            decision_context="important operation",
            contract_reference=contract_ref,
            capability_reference="critical.cap",
            requested_by="admin",
        )
        r = repr(request)
        assert "important" in r
        assert "critical.cap" in r


# ── ApprovalDecision Tests ──────────────────────

class TestApprovalDecision:
    """Tests for ApprovalDecision model."""

    def test_create_decision(self):
        decision = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="All checks passed",
            approval_id="test-001",
            decided_at=time.time(),
            decided_by="system",
        )
        assert decision.state == ApprovalDecisionState.APPROVED
        assert decision.decision_reason == "All checks passed"

    def test_approved_factory(self):
        decision = ApprovalDecision.approved(
            approval_id="test-002",
            reason="All clear",
        )
        assert decision.state == ApprovalDecisionState.APPROVED
        assert decision.is_approved() is True
        assert decision.permits_execution() is True

    def test_rejected_factory(self):
        decision = ApprovalDecision.rejected(
            approval_id="test-003",
            reason="Security violation",
        )
        assert decision.state == ApprovalDecisionState.REJECTED
        assert decision.is_rejected() is True
        assert decision.permits_execution() is False

    def test_expired_factory(self):
        decision = ApprovalDecision.expired("test-004")
        assert decision.state == ApprovalDecisionState.EXPIRED
        assert decision.is_expired() is True
        assert decision.permits_execution() is False

    def test_cancelled_factory(self):
        decision = ApprovalDecision.cancelled("test-005")
        assert decision.state == ApprovalDecisionState.CANCELLED
        assert decision.is_cancelled() is True

    def test_superseded_factory(self):
        decision = ApprovalDecision.superseded("test-006")
        assert decision.state == ApprovalDecisionState.SUPERSEDED
        assert decision.is_superseded() is True

    def test_is_approved(self):
        d = ApprovalDecision.approved("id", "ok")
        assert d.is_approved() is True
        assert d.is_rejected() is False
        assert d.is_expired() is False

    def test_is_rejected(self):
        d = ApprovalDecision.rejected("id", "no")
        assert d.is_rejected() is True
        assert d.is_approved() is False

    def test_permits_execution_only_approved(self):
        approved = ApprovalDecision.approved("a", "ok")
        rejected = ApprovalDecision.rejected("r", "no")
        expired = ApprovalDecision.expired("e")
        cancelled = ApprovalDecision.cancelled("c")

        assert approved.permits_execution() is True
        assert rejected.permits_execution() is False
        assert expired.permits_execution() is False
        assert cancelled.permits_execution() is False

    def test_validate_valid_decision(self):
        d = ApprovalDecision.approved("id", "valid reason")
        assert d.validate() is True

    def test_validate_empty_reason(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="",
            approval_id="id",
            decided_at=time.time(),
            decided_by="system",
        )
        assert d.validate() is False

    def test_validate_empty_approval_id(self):
        d = ApprovalDecision(
            state=ApprovalDecisionState.APPROVED,
            decision_reason="reason",
            approval_id="",
            decided_at=time.time(),
            decided_by="system",
        )
        assert d.validate() is False

    def test_decision_is_frozen(self):
        d = ApprovalDecision.approved("id", "ok")
        with pytest.raises(Exception):
            d.state = ApprovalDecisionState.REJECTED  # type: ignore

    def test_repr_contains_state_and_reason(self):
        d = ApprovalDecision.approved("abc", "everything passed")
        r = repr(d)
        assert "APPROVED" in r
        assert "everything passed" in r

    def test_enum_has_all_six_states(self):
        states = list(ApprovalDecisionState)
        assert len(states) == 5  # APPROVED, REJECTED, EXPIRED, CANCELLED, SUPERSEDED

    def test_metadata_field(self):
        d = ApprovalDecision.approved(
            "id", "ok", metadata={"policy": "default"}
        )
        assert d.metadata == {"policy": "default"}
