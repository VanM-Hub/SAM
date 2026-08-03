"""Tests for compliance exceptions."""

import pytest
from sam.compliance.exceptions.compliance_errors import (
    ComplianceError,
    CheckNotFoundError,
    DuplicateCheckError,
    CheckExecutionError,
    InvalidSessionStateError,
    SessionImmutableError,
    VerdictComputationError,
    RegistryError,
    EvidenceCollectionError,
    ReportGenerationError,
    LifecycleError,
)


class TestExceptions:
    """All exception types must be constructable and chain properly."""

    def test_check_not_found(self):
        e = CheckNotFoundError("ABC")
        assert "ABC" in str(e)
        assert e.check_id == "ABC"
        assert isinstance(e, ComplianceError)

    def test_duplicate_check(self):
        e = DuplicateCheckError("DEF")
        assert "DEF" in str(e)
        assert e.check_id == "DEF"

    def test_check_execution_error(self):
        e = CheckExecutionError("T01", "simulated error")
        assert "T01" in str(e)
        assert "simulated error" in str(e)
        assert e.check_id == "T01"
        assert e.original_error == "simulated error"

    def test_check_execution_error_no_original(self):
        e = CheckExecutionError("T01")
        assert "T01" in str(e)

    def test_invalid_session_state(self):
        e = InvalidSessionStateError("ANALYSIS", "INITIATED")
        assert "ANALYSIS" in str(e)
        assert e.current_state == "ANALYSIS"

    def test_session_immutable(self):
        e = SessionImmutableError("sess-1")
        assert "sess-1" in str(e)
        assert e.session_id == "sess-1"

    def test_verdict_computation_error(self):
        e = VerdictComputationError("No findings provided")
        assert "No findings provided" in str(e)
        assert e.reason == "No findings provided"

    def test_registry_error(self):
        e = RegistryError("Invalid check format")
        assert "Invalid check format" in str(e)

    def test_evidence_collection_error(self):
        e = EvidenceCollectionError("L1-C01", "File not readable")
        assert "L1-C01" in str(e)
        assert "File not readable" in str(e)
        assert e.check_id == "L1-C01"

    def test_report_generation_error(self):
        e = ReportGenerationError("Missing section data")
        assert "Missing section data" in str(e)

    def test_lifecycle_error(self):
        e = LifecycleError("State locked")
        assert "State locked" in str(e)

    def test_all_exceptions_are_compliance_error(self):
        exceptions = [
            CheckNotFoundError("A"),
            DuplicateCheckError("B"),
            CheckExecutionError("C"),
            InvalidSessionStateError("D", "E"),
            SessionImmutableError("F"),
            VerdictComputationError("G"),
            RegistryError("H"),
            EvidenceCollectionError("I", "J"),
            ReportGenerationError("K"),
            LifecycleError("L"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ComplianceError)


class TestExceptionMessages:
    """Exception messages are informative."""

    def test_messages_contain_context(self):
        e1 = CheckNotFoundError("L0-01")
        assert "L0-01" in str(e1)

        e2 = DuplicateCheckError("L0-01")
        assert "L0-01" in str(e2)
        assert "already" in str(e2).lower()

        e3 = CheckExecutionError("T99", "RuntimeError: boom")
        assert "T99" in str(e3)
        assert "boom" in str(e3)
