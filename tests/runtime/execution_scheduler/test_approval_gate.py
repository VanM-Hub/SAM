"""Tests: Approval Gate — Execution only when Approval = Approved.

Per I6 invariant: Execution performs only after approval.
"""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    InvalidApprovalError,
)
from src.sam.runtime.execution_scheduler.validation.approval_validator import (
    ApprovalValidator,
)


class TestApprovalValidator:
    def test_approved_passes(self):
        assert ApprovalValidator.validate_approved("APPROVED") is True

    def test_rejected_fails(self):
        assert ApprovalValidator.validate_approved("REJECTED") is False

    def test_pending_fails(self):
        assert ApprovalValidator.validate_approved("PENDING") is False

    def test_expired_fails(self):
        assert ApprovalValidator.validate_approved("EXPIRED") is False

    def test_none_fails(self):
        assert ApprovalValidator.validate_approved(None) is False

    def test_case_insensitive(self):
        assert ApprovalValidator.validate_approved("approved") is True
        assert ApprovalValidator.validate_approved("Approved") is True

    def test_validate_approval_reference_valid(self):
        assert ApprovalValidator.validate_approval_reference("appr-001") is True

    def test_validate_approval_reference_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ApprovalValidator.validate_approval_reference("")

    def test_validate_approval_reference_whitespace_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ApprovalValidator.validate_approval_reference("   ")


class TestApprovalGate:
    def test_approved_creates(self):
        svc = SchedulerService()
        svc.initialize()
        identity = svc.create_execution(
            ExecutionRequest("a1", "c1", "cp1"),
            approval_state="APPROVED",
        )
        assert identity is not None

    def test_rejected_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(InvalidApprovalError):
            svc.create_execution(
                ExecutionRequest("a1", "c1", "cp1"),
                approval_state="REJECTED",
            )

    def test_expired_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(InvalidApprovalError):
            svc.create_execution(
                ExecutionRequest("a1", "c1", "cp1"),
                approval_state="EXPIRED",
            )

    def test_cancelled_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(InvalidApprovalError):
            svc.create_execution(
                ExecutionRequest("a1", "c1", "cp1"),
                approval_state="CANCELLED",
            )

    def test_pending_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(InvalidApprovalError):
            svc.create_execution(
                ExecutionRequest("a1", "c1", "cp1"),
                approval_state="PENDING",
            )

    def test_superseded_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(InvalidApprovalError):
            svc.create_execution(
                ExecutionRequest("a1", "c1", "cp1"),
                approval_state="SUPERSEDED",
            )
