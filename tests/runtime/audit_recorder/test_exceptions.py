"""Test Audit Recorder exceptions.

All 9 exception types defined in AUDIT_SPEC §Failure Behaviour
and internal errors.
"""

import pytest


class TestExceptions:
    """Verify all exception types are defined and behave correctly."""

    def test_missing_reference_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            MissingReferenceError,
            AuditRecorderError,
        )
        assert issubclass(MissingReferenceError, AuditRecorderError)
        e = MissingReferenceError("execution_reference missing")
        assert "execution_reference" in str(e)

    def test_broken_traceability_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            BrokenTraceabilityError,
            AuditRecorderError,
        )
        assert issubclass(BrokenTraceabilityError, AuditRecorderError)
        e = BrokenTraceabilityError("chain broken at approval")
        assert "chain broken" in str(e)

    def test_incomplete_record_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            IncompleteRecordError,
            AuditRecorderError,
        )
        assert issubclass(IncompleteRecordError, AuditRecorderError)
        e = IncompleteRecordError("missing outcome")
        assert "missing" in str(e)

    def test_invalid_record_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            InvalidRecordError,
            AuditRecorderError,
        )
        assert issubclass(InvalidRecordError, AuditRecorderError)
        e = InvalidRecordError("malformed record")
        assert "malformed" in str(e)

    def test_duplicate_record_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            DuplicateRecordError,
            AuditRecorderError,
        )
        assert issubclass(DuplicateRecordError, AuditRecorderError)
        e = DuplicateRecordError("audit-exec-001 already exists")
        assert "already exists" in str(e)

    def test_archived_reference_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            ArchivedReferenceError,
            AuditRecorderError,
        )
        assert issubclass(ArchivedReferenceError, AuditRecorderError)
        e = ArchivedReferenceError("reference is archived")
        assert "archived" in str(e)

    def test_audit_not_found_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            AuditNotFoundError,
            AuditRecorderError,
        )
        assert issubclass(AuditNotFoundError, AuditRecorderError)
        e = AuditNotFoundError("audit-xyz not found")
        assert "not found" in str(e)

    def test_archive_conflict_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            ArchiveConflictError,
            AuditRecorderError,
        )
        assert issubclass(ArchiveConflictError, AuditRecorderError)
        e = ArchiveConflictError("already archived")
        assert "archived" in str(e)

    def test_verification_failure_error(self):
        from src.sam.runtime.audit_recorder.exceptions.audit_errors import (
            VerificationFailureError,
            AuditRecorderError,
        )
        assert issubclass(VerificationFailureError, AuditRecorderError)
        e = VerificationFailureError("traceability broken")
        assert "traceability" in str(e)

    def test_all_errors_inherit_base(self):
        """All exceptions inherit from AuditRecorderError."""
        from src.sam.runtime.audit_recorder.exceptions import audit_errors as ae
        base = ae.AuditRecorderError
        for name in dir(ae):
            obj = getattr(ae, name)
            if isinstance(obj, type) and issubclass(obj, Exception) and obj is not base:
                assert issubclass(obj, base), f"{name} should inherit AuditRecorderError"
