"""Tests: Verification — verify execution preconditions."""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    VerificationFailureError,
    ExecutionNotFoundError,
    NotOperationalError,
)
from src.sam.runtime.execution_scheduler.validation.verification_validator import (
    VerificationValidator,
)


class TestVerificationValidator:
    def test_valid_preconditions(self):
        result = VerificationValidator.verify_preconditions(
            "appr-001", "ctr-001", "cap-001",
        )
        assert result["verified"] is True
        assert result["errors"] == []

    def test_empty_approval_ref_fails(self):
        with pytest.raises(ValueError, match="approval"):
            VerificationValidator.verify_preconditions("", "ctr-001", "cap-001")

    def test_empty_contract_ref_fails(self):
        with pytest.raises(ValueError, match="contract"):
            VerificationValidator.verify_preconditions("appr-001", "", "cap-001")

    def test_empty_capability_ref_fails(self):
        with pytest.raises(ValueError, match="capability"):
            VerificationValidator.verify_preconditions("appr-001", "ctr-001", "")

    def test_all_three_empty_fails(self):
        with pytest.raises(ValueError):
            VerificationValidator.verify_preconditions("", "", "")

    def test_is_verified_true(self):
        result = {"verified": True}
        assert VerificationValidator.is_verified(result) is True

    def test_is_verified_false(self):
        result = {"verified": False, "errors": ["bad"]}
        assert VerificationValidator.is_verified(result) is False


class TestServiceVerification:
    def test_verify_execution(self):
        svc = SchedulerService()
        svc.initialize()
        identity = svc.create_execution(
            ExecutionRequest("appr-001", "ctr-001", "cap-001"),
            approval_state="APPROVED",
        )
        result = svc.verify(identity.execution_id)
        assert result["verified"] is True

    def test_verify_nonexistent_raises(self):
        svc = SchedulerService()
        svc.initialize()
        with pytest.raises(ExecutionNotFoundError):
            svc.verify("nonexistent")

    def test_verify_not_operational_raises(self):
        svc = SchedulerService()
        with pytest.raises(NotOperationalError):
            svc.verify("any")

    def test_verify_after_transition(self):
        svc = SchedulerService()
        svc.initialize()
        identity = svc.create_execution(
            ExecutionRequest("appr-001", "ctr-001", "cap-001"),
            approval_state="APPROVED",
        )
        svc.schedule(identity.execution_id)
        svc.transition(identity.execution_id, "RUNNING")
        # Verification should still work in RUNNING state
        result = svc.verify(identity.execution_id)
        assert result["verified"] is True

    def test_verify_stores_metadata(self):
        svc = SchedulerService()
        svc.initialize()
        identity = svc.create_execution(
            ExecutionRequest("appr-001", "ctr-001", "cap-001"),
            approval_state="APPROVED",
        )
        svc.verify(identity.execution_id)
        record = svc.get(identity.execution_id)
        assert "verified" in record.metadata
        assert "verification_timestamp" in record.metadata
