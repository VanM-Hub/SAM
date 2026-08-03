"""Test all Audit Recorder validators."""

import pytest
from src.sam.runtime.audit_recorder.validation.record_validator import (
    validate_record_input,
    validate_no_duplicate,
)
from src.sam.runtime.audit_recorder.validation.lifecycle_validator import (
    validate_recorder_lifecycle_transition,
    validate_audit_record_transition,
)
from src.sam.runtime.audit_recorder.lifecycle.recorder_lifecycle import (
    RecorderLifecycleState,
)
from src.sam.runtime.audit_recorder.state.audit_state import AuditRecordState


class FakeResult:
    def __init__(self, exec_id, approval="a", contract="c", capability="cp",
                 state="COMPLETED", metadata=None):
        self.execution_id = exec_id
        self.approval_reference = approval
        self.contract_reference = contract
        self.capability_reference = capability
        self.citizen_reference = "citizen"
        self.state = state
        self.message = "ok"
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "execution_id": self.execution_id,
            "approval_reference": self.approval_reference,
            "contract_reference": self.contract_reference,
            "capability_reference": self.capability_reference,
            "citizen_reference": self.citizen_reference,
        }


class TestRecordValidator:
    """Test record compilation validators."""

    def test_valid_input_passes(self):
        r = FakeResult("exec-001")
        errors = validate_record_input(r)
        assert len(errors) == 0

    def test_none_input_fails(self):
        errors = validate_record_input(None)
        assert len(errors) > 0

    def test_missing_execution_id(self):
        r = FakeResult("")
        errors = validate_record_input(r)
        assert any("execution_id" in e for e in errors)

    def test_missing_approval_reference(self):
        r = FakeResult("exec-001", approval="")
        errors = validate_record_input(r)
        assert any("approval" in e for e in errors)

    def test_missing_contract_reference(self):
        r = FakeResult("exec-001", contract="")
        errors = validate_record_input(r)
        assert any("contract" in e for e in errors)

    def test_no_duplicate(self):
        errors = validate_no_duplicate("audit-001", {})
        assert len(errors) == 0

    def test_duplicate_detected(self):
        errors = validate_no_duplicate("audit-001", {"audit-001": True})
        assert len(errors) > 0
        assert "already exists" in errors[0]


class TestLifecycleValidators:
    """Test lifecycle transition validators."""

    def test_valid_recorder_transition(self):
        errors = validate_recorder_lifecycle_transition(
            RecorderLifecycleState.RUNNING,
            RecorderLifecycleState.STOPPING,
        )
        assert len(errors) == 0

    def test_invalid_recorder_transition(self):
        errors = validate_recorder_lifecycle_transition(
            RecorderLifecycleState.RUNNING,
            RecorderLifecycleState.UNINITIALIZED,
        )
        assert len(errors) > 0

    def test_valid_audit_transition(self):
        errors = validate_audit_record_transition(
            AuditRecordState.RECORDED,
            AuditRecordState.VERIFIED,
        )
        assert len(errors) == 0

    def test_invalid_audit_transition(self):
        errors = validate_audit_record_transition(
            AuditRecordState.ARCHIVED,
            AuditRecordState.RECORDED,
        )
        assert len(errors) > 0

    def test_none_current_state(self):
        errors = validate_recorder_lifecycle_transition(
            None, RecorderLifecycleState.RUNNING
        )
        assert len(errors) > 0

    def test_none_target_state(self):
        errors = validate_recorder_lifecycle_transition(
            RecorderLifecycleState.RUNNING, None
        )
        assert len(errors) > 0
