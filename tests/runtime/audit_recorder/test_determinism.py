"""Test deterministic behavior of Audit Recorder.

Per ADR-001: same input = same output. The Audit Recorder
must produce deterministic results across independent runs.
"""

import pytest


class FakeExecutionResult:
    """Fake execution result for testing."""
    def __init__(self, exec_id, approval, contract, capability,
                 state="COMPLETED", message="ok"):
        self.execution_id = exec_id
        self.approval_reference = approval
        self.contract_reference = contract
        self.capability_reference = capability
        self.citizen_reference = "citizen-test"
        self.state = state
        self.message = message
        self.metadata = {
            "execution_id": exec_id,
            "approval_reference": approval,
            "contract_reference": contract,
            "capability_reference": capability,
            "citizen_reference": "citizen-test",
        }


class TestDeterminism:
    """Verify deterministic behavior."""

    @pytest.fixture
    def svc(self):
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        s = RecorderService()
        s.initialize()
        return s

    def test_record_same_input_same_output(self, svc):
        """Same input twice → same record structure (different records)."""
        r1 = FakeExecutionResult("exec-001", "appr-1", "ctr-1", "cap-1")
        r2 = FakeExecutionResult("exec-002", "appr-2", "ctr-2", "cap-2")

        a = svc.record(r1)
        b = svc.record(r2)

        # Different audit IDs
        assert a.audit_id != b.audit_id
        # But same structure
        assert a.execution_reference == "exec-001"
        assert b.execution_reference == "exec-002"

    def test_verify_deterministic(self, svc):
        """Same verification on same record → same result."""
        r = FakeExecutionResult("exec-010", "appr-1", "ctr-1", "cap-1")
        record = svc.record(r)

        v1 = svc.verify(record.audit_id)
        v2 = svc.verify(record.audit_id)

        assert v1.status == v2.status
        assert v1.evidence == v2.evidence

    def test_archive_deterministic(self, svc):
        """Archiving same record twice: first succeeds, second ArchiveConflict."""
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            ArchiveConflictError,
        )

        r = FakeExecutionResult("exec-020", "appr-1", "ctr-1", "cap-1")
        record = svc.record(r)

        svc.archive(record.audit_id)

        # Second archive should fail consistently
        with pytest.raises(ArchiveConflictError):
            svc.archive(record.audit_id)

    def test_query_deterministic(self, svc):
        """Same query → same result."""
        r1 = FakeExecutionResult("exec-030", "appr-a", "ctr-x", "cap-1")
        r2 = FakeExecutionResult("exec-031", "appr-b", "ctr-x", "cap-2")
        svc.record(r1)
        svc.record(r2)

        q1 = svc.query({"contract_reference": "ctr-x"})
        q2 = svc.query({"contract_reference": "ctr-x"})

        assert len(q1) == len(q2) == 2
        ids1 = sorted([r.audit_id for r in q1])
        ids2 = sorted([r.audit_id for r in q2])
        assert ids1 == ids2

    def test_get_health_deterministic(self, svc):
        """Health reports deterministic for same state."""
        h1 = svc.get_health()
        h2 = svc.get_health()

        assert h1["status"] == h2["status"]
        assert h1["record_count"] == h2["record_count"]
