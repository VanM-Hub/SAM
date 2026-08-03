"""Audit Recorder exceptions — AUDIT_SPEC §Failure Behaviour.

Defined failures per AUDIT_SPEC L129-L140:
- MissingReference: a required reference is absent
- BrokenTraceability: a record cannot be followed back to its origin
- IncompleteRecord: the record lacks required elements
- InvalidRecord: the record is malformed or invalid
- DuplicateRecord: an identical record already exists
- ArchivedReference: a referenced object has been archived and can no longer be verified

Additional internal errors:
- AuditNotFoundError: no audit record with the given ID
- ArchiveConflictError: cannot archive an already-archived record
- VerificationFailureError: verification of a record failed
"""


class AuditRecorderError(Exception):
    """Base exception for all Audit Recorder errors."""
    pass


class MissingReferenceError(AuditRecorderError):
    """A required traceability reference is absent.

    Per AUDIT_SPEC L131: all records must reference
    Execution, Approval, Contract, Capability, and Citizen.
    """
    pass


class BrokenTraceabilityError(AuditRecorderError):
    """A record cannot be followed back to its origin.

    Per AUDIT_SPEC L132: the chain of references is broken.
    """
    pass


class IncompleteRecordError(AuditRecorderError):
    """The record lacks required elements.

    Per AUDIT_SPEC L133: the record is structurally incomplete.
    """
    pass


class InvalidRecordError(AuditRecorderError):
    """The record is malformed or invalid.

    Per AUDIT_SPEC L134: the record does not pass validity checks.
    """
    pass


class DuplicateRecordError(AuditRecorderError):
    """An identical record already exists.

    Per AUDIT_SPEC L135: duplicate audit records are not permitted.
    """
    pass


class ArchivedReferenceError(AuditRecorderError):
    """A referenced object has been archived and can no longer be verified.

    Per AUDIT_SPEC L136: archived references cannot be re-verified.
    """
    pass


class AuditNotFoundError(AuditRecorderError):
    """No audit record exists with the given audit ID."""
    pass


class ArchiveConflictError(AuditRecorderError):
    """Cannot archive an already-archived record.

    Per AUDIT_SPEC L98: Archived is terminal.
    """
    pass


class VerificationFailureError(AuditRecorderError):
    """Verification of an audit record failed.

    The record remains in RECORDED state and the verification
    evidence explains why it could not be verified.
    """
    pass
