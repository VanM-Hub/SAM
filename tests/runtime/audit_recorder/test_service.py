"""Test RecorderService core operations.

Covers: record, archive, get, query, verify, get_health.
"""

import pytest
from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
    AuditNotFoundError,
    ArchiveConflictError,
    DuplicateRecordError,
    IncompleteRecordError,
    InvalidRecordError,
    VerificationFailureError,
)
from src.sam.runtime.audit_recorder.services.recorder_service import RecorderService
from src.sam.runtime.audit_recorder.state.audit_state import AuditRecordState


class FakeExecutionResult:
    """Fake execution result mimicking Execution Scheduler output."""
    def __init__(self, exec_id, approval="appr-001", contract="ctr-001",
                 capability="cap-001", state="COMPLETED", message="ok",
                 citizen="cit-001"):
        self.execution_id = exec_id
        self.approval_reference = approval
        self.contract_reference = contract
        self.capability_reference = capability
        self.citizen_reference = citizen
        self.state = state if hasattr(state, "value") else state
        self.message = message
        self.metadata = {
            "execution_id": exec_id,
            "approval_reference": approval,
            "contract_reference": contract,
            "capability_reference": capability,
            "citizen_reference": citizen,
        }

    def to_dict(self):
        return {
            "execution_id": self.execution_id,
            "approval_reference": self.approval_reference,
            "contract_reference": self.contract_reference,
            "capability_reference": self.capability_reference,
            "citizen_reference": self.citizen_reference,
        }


class TestRecorderService:
    """Core service tests."""

    @pytest.fixture
    def svc(self):
        s = RecorderService()
        s.initialize()
        return s

    def test_record_basic(self, svc):
        """Record a basic execution result."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        assert record.audit_id is not None
        assert record.outcome is not None
        assert svc.record_count == 1

    def test_record_increases_count(self, svc):
        """Recording multiple increases count."""
        svc.record(FakeExecutionResult("exec-001"))
        svc.record(FakeExecutionResult("exec-002"))
        assert svc.record_count == 2

    def test_record_duplicate_raises(self, svc):
        """Recording same execution twice raises DuplicateRecordError."""
        result = FakeExecutionResult("exec-001")
        svc.record(result)
        with pytest.raises(DuplicateRecordError):
            svc.record(result)

    def test_record_external_source_rejected(self, svc):
        """ADR-006: external source is rejected."""
        result = FakeExecutionResult("exec-001")
        with pytest.raises(InvalidRecordError):
            svc.record(result, input_source="external_api")

    def test_record_internal_source_accepted(self, svc):
        """Execution scheduler source is accepted."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result, input_source="execution_scheduler")
        assert record is not None

    def test_get_existing_record(self, svc):
        """Get returns the recorded audit record."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        fetched = svc.get(record.audit_id)
        assert fetched.audit_id == record.audit_id

    def test_get_nonexistent_raises(self, svc):
        """Get on unknown ID raises AuditNotFoundError."""
        with pytest.raises(AuditNotFoundError):
            svc.get("nonexistent-id")

    def test_archive_from_recorded(self, svc):
        """Archive a RECORDED record."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        archived = svc.archive(record.audit_id)
        assert archived.audit_id == record.audit_id
        assert svc.get_record_state(record.audit_id) == AuditRecordState.ARCHIVED

    def test_archive_already_archived_raises(self, svc):
        """Archiving an ARCHIVED record raises ArchiveConflictError."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        svc.archive(record.audit_id)
        with pytest.raises(ArchiveConflictError):
            svc.archive(record.audit_id)

    def test_archive_nonexistent_raises(self, svc):
        """Archive on unknown ID raises AuditNotFoundError."""
        with pytest.raises(AuditNotFoundError):
            svc.archive("nonexistent-id")

    def test_query_all(self, svc):
        """Query with no filters returns all records."""
        svc.record(FakeExecutionResult("exec-001"))
        svc.record(FakeExecutionResult("exec-002"))
        results = svc.query()
        assert len(results) == 2

    def test_query_by_outcome(self, svc):
        """Query by outcome filter."""
        from src.sam.runtime.execution_scheduler.models.execution_result import ExecutionResultState
        r1 = FakeExecutionResult("exec-001", state="COMPLETED")
        r2 = FakeExecutionResult("exec-002", state="FAILED")
        svc.record(r1)
        svc.record(r2)

        results = svc.query({"outcome": "COMPLETED"})
        assert len(results) == 1
        assert results[0].execution_reference == "exec-001"

    def test_query_by_contract_reference(self, svc):
        """Query by contract reference."""
        svc.record(FakeExecutionResult("exec-001", contract="ctr-a"))
        svc.record(FakeExecutionResult("exec-002", contract="ctr-b"))
        svc.record(FakeExecutionResult("exec-003", contract="ctr-a"))

        results = svc.query({"contract_reference": "ctr-a"})
        assert len(results) == 2

    def test_query_empty_filters(self, svc):
        """Query with empty dict returns all."""
        svc.record(FakeExecutionResult("exec-001"))
        assert len(svc.query({})) == 1

    def test_verify_basic(self, svc):
        """Verify a recorded audit record."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        v = svc.verify(record.audit_id)
        assert v.is_verified() is True
        assert "intact" in v.evidence

    def test_verify_transitions_to_verified(self, svc):
        """Verification transitions from RECORDED to VERIFIED."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        svc.verify(record.audit_id)
        assert svc.get_record_state(record.audit_id) == AuditRecordState.VERIFIED

    def test_verify_archived_record_fails(self, svc):
        """Cannot verify an ARCHIVED record."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        svc.archive(record.audit_id)
        with pytest.raises(VerificationFailureError):
            svc.verify(record.audit_id)

    def test_verify_nonexistent_raises(self, svc):
        """Verify on unknown ID raises AuditNotFoundError."""
        with pytest.raises(AuditNotFoundError):
            svc.verify("nonexistent-id")

    def test_get_health_basic(self, svc):
        """Health returns basic structure."""
        health = svc.get_health()
        assert health["status"] == "HEALTHY"
        assert health["unit"] == "audit_recorder"
        assert "record_count" in health
        assert "archived_count" in health
        assert "verified_count" in health
        assert "recorded_count" in health

    def test_get_health_reflects_state(self, svc):
        """Health counts reflect actual record states."""
        r1 = FakeExecutionResult("exec-001")
        svc.record(r1)
        health = svc.get_health()
        assert health["recorded_count"] == 1
        assert health["verified_count"] == 0
        assert health["archived_count"] == 0

    def test_get_record_state(self, svc):
        """get_record_state returns correct state."""
        result = FakeExecutionResult("exec-001")
        record = svc.record(result)
        assert svc.get_record_state(record.audit_id) == AuditRecordState.RECORDED

    def test_get_state_counts(self, svc):
        """get_state_counts returns correct tallies."""
        r1 = FakeExecutionResult("exec-001")
        r2 = FakeExecutionResult("exec-002")
        svc.record(r1)
        svc.record(r2)
        svc.archive(f"audit-{r1.execution_id}")

        counts = svc.get_state_counts()
        assert counts["RECORDED"] == 1
        assert counts["ARCHIVED"] == 1

    def test_query_by_verification_status(self, svc):
        """Query by verification status."""
        r1 = FakeExecutionResult("exec-001")
        r2 = FakeExecutionResult("exec-002")
        svc.record(r1)
        svc.record(r2)
        svc.verify(f"audit-{r1.execution_id}")

        verified = svc.query({"verification_status": "VERIFIED"})
        assert len(verified) == 1
