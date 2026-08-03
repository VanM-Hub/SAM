"""Test archive workflow.

Per AUDIT_SPEC L93-L98:
- Recorded → Archived (skip verification)
- Verified → Archived
- Archived is terminal
"""

import pytest
from src.sam.runtime.audit_recorder.validation.archive_validator import (
    validate_archive_eligibility,
    validate_archive_completeness,
)
from src.sam.runtime.audit_recorder.state.audit_state import AuditRecordState
from src.sam.runtime.audit_recorder.services.recorder_service import (
    RecorderService,
)


class FakeResult:
    def __init__(self, exec_id, approval="appr-001", contract="ctr-001",
                 capability="cap-001", state="COMPLETED"):
        self.execution_id = exec_id
        self.approval_reference = approval
        self.contract_reference = contract
        self.capability_reference = capability
        self.citizen_reference = "cit-001"
        self.state = state
        self.message = "ok"
        self.metadata = {
            "execution_id": exec_id,
            "approval_reference": approval,
            "contract_reference": contract,
            "capability_reference": capability,
            "citizen_reference": "cit-001",
        }


class FakeRecord:
    def __init__(self, identity, outcome="COMPLETED", state=AuditRecordState.RECORDED):
        self.identity = identity
        self.outcome = outcome
        self._state = state


class TestArchiveValidator:
    """Test archive validation rules."""

    def test_recorded_eligible(self):
        from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r = FakeRecord(identity, state=AuditRecordState.RECORDED)
        errors = validate_archive_eligibility(r)
        assert len(errors) == 0

    def test_verified_eligible(self):
        from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r = FakeRecord(identity, state=AuditRecordState.VERIFIED)
        errors = validate_archive_eligibility(r)
        assert len(errors) == 0

    def test_archived_not_eligible(self):
        from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r = FakeRecord(identity, state=AuditRecordState.ARCHIVED)
        errors = validate_archive_eligibility(r)
        assert len(errors) > 0
        assert "already" in errors[0].lower()

    def test_none_record_not_eligible(self):
        errors = validate_archive_eligibility(None)
        assert len(errors) > 0

    def test_completeness_valid(self):
        from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r = FakeRecord(identity, outcome="COMPLETED")
        errors = validate_archive_completeness(r)
        assert len(errors) == 0

    def test_completeness_no_identity(self):
        r = FakeRecord(None)
        errors = validate_archive_completeness(r)
        assert len(errors) > 0
        assert any("identity" in e.lower() for e in errors)


class TestArchiveService:
    """Integration tests for archive workflow."""

    def test_archive_from_recorded(self):
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        archived = s.archive(r.audit_id)
        assert archived is not None
        assert s.get_record_state(r.audit_id) == AuditRecordState.ARCHIVED

    def test_archive_from_verified(self):
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        s.verify(r.audit_id)
        archived = s.archive(r.audit_id)
        assert s.get_record_state(r.audit_id) == AuditRecordState.ARCHIVED

    def test_archive_terminal_no_further_transition(self):
        """After archive, cannot verify again."""
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            VerificationFailureError,
        )
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        s.archive(r.audit_id)
        with pytest.raises(VerificationFailureError):
            s.verify(r.audit_id)

    def test_archive_preserves_data(self):
        """Archived record retains original data."""
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        original_audit_id = r.audit_id
        original_outcome = r.outcome

        s.archive(r.audit_id)
        fetched = s.get(r.audit_id)
        assert fetched.audit_id == original_audit_id
        assert fetched.outcome == original_outcome
