"""Test boundary validation — ADR-006.

Audit Recorder has no external access. Only accepts
input from internal Runtime units.
"""

import pytest
from src.sam.runtime.audit_recorder.validation.boundary_validator import (
    validate_boundary,
    validate_no_external_output,
)


class TestBoundaryValidator:
    """Verify boundary enforcement per ADR-006."""

    def test_execution_scheduler_accepted(self):
        errors = validate_boundary("execution_scheduler")
        assert len(errors) == 0

    def test_runtime_internal_accepted(self):
        errors = validate_boundary("runtime_internal")
        assert len(errors) == 0

    def test_internal_accepted(self):
        errors = validate_boundary("internal")
        assert len(errors) == 0

    def test_external_client_rejected(self):
        errors = validate_boundary("external_client")
        assert len(errors) > 0
        assert "Boundary" in errors[0]

    def test_arbitrary_string_rejected(self):
        errors = validate_boundary("some_random_api")
        assert len(errors) > 0

    def test_empty_source_rejected(self):
        errors = validate_boundary("")
        assert len(errors) > 0

    def test_none_source_rejected(self):
        errors = validate_boundary(None)
        assert len(errors) > 0

    def test_no_external_output_valid(self):
        """validate_no_external_output always returns empty."""
        errors = validate_no_external_output(None)
        assert len(errors) == 0

    def test_boundary_in_service(self):
        """Boundary check integrated into RecorderService.record()."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            InvalidRecordError,
        )

        class FakeResult:
            execution_id = "exec-001"
            approval_reference = "appr-001"
            contract_reference = "ctr-001"
            capability_reference = "cap-001"
            state = "COMPLETED"

        s = RecorderService()
        s.initialize()

        # Valid: execution_scheduler
        r = s.record(FakeResult(), input_source="execution_scheduler")
        assert r is not None

        # Invalid: external
        with pytest.raises(InvalidRecordError, match="Boundary"):
            s.record(FakeResult(), input_source="external_service")
