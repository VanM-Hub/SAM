"""Test immutability invariants.

Per AUDIT_SPEC: audit records are immutable. Once recorded,
they cannot be changed. Verification adds a result but does
not modify the original data.
"""

import pytest
from src.sam.runtime.audit_recorder.models.audit_identity import AuditIdentity
from src.sam.runtime.audit_recorder.models.audit_record import AuditRecord
from src.sam.runtime.audit_recorder.validation.invariant_validator import (
    validate_immutability,
    validate_no_feedback,
    validate_no_external_access,
)
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


class TestImmutability:
    """Verify audit record immutability invariants."""

    def test_records_are_frozen_dataclass(self):
        """AuditRecord is a frozen dataclass — cannot modify attributes."""
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        record = AuditRecord(identity=identity, outcome="COMPLETED")
        with pytest.raises(Exception):
            record.outcome = "CHANGED"

    def test_identity_is_frozen_dataclass(self):
        """AuditIdentity is a frozen dataclass."""
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        with pytest.raises(Exception):
            identity.execution_reference = "changed"

    def test_immutability_validator_same_data(self):
        """Two identical records pass immutability check."""
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r1 = AuditRecord(identity=identity, outcome="COMPLETED")
        r2 = AuditRecord(identity=identity, outcome="COMPLETED")
        errors = validate_immutability(r1, r2)
        assert len(errors) == 0

    def test_immutability_validator_different_outcome(self):
        """Different outcomes flag immutability violation."""
        identity = AuditIdentity(
            audit_id="audit-001",
            execution_reference="exec-001",
            approval_reference="appr-001",
            contract_reference="ctr-001",
            capability_reference="cap-001",
            citizen_reference="cit-001",
            timestamp="2026-08-03T10:00:00",
        )
        r1 = AuditRecord(identity=identity, outcome="COMPLETED")
        r2 = AuditRecord(identity=identity, outcome="FAILED")
        errors = validate_immutability(r1, r2)
        assert len(errors) > 0
        assert any("outcome" in e for e in errors)

    def test_immutability_validator_none(self):
        """None inputs return empty errors."""
        errors = validate_immutability(None, None)
        assert len(errors) == 0

    def test_no_feedback_guard(self):
        """validate_no_feedback is a structural guard."""
        errors = validate_no_feedback(None)
        assert len(errors) == 0

    def test_no_external_access_guard(self):
        """validate_no_external_access is a structural guard."""
        errors = validate_no_external_access(None)
        assert len(errors) == 0

    def test_get_after_recording_returns_same_data(self):
        """Service.get() returns identical data after recording."""
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))

        fetched = s.get(r.audit_id)
        assert fetched.audit_id == r.audit_id
        assert fetched.outcome == r.outcome
        assert fetched.execution_reference == r.execution_reference

    def test_verify_does_not_change_outcome(self):
        """Verification adds result but doesn't change the record data."""
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        original_outcome = r.outcome

        s.verify(r.audit_id)
        fetched = s.get(r.audit_id)
        assert fetched.outcome == original_outcome

    def test_archive_does_not_change_identity(self):
        """Archived record retains its identity."""
        s = RecorderService()
        s.initialize()
        r = s.record(FakeResult("exec-001"))
        original_id = r.identity

        s.archive(r.audit_id)
        fetched = s.get(r.audit_id)
        assert fetched.identity == original_id
