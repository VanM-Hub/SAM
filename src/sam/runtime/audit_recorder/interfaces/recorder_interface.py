"""RecorderInterface — Public API Protocol.

6 public methods per I0-001 §2.7:
- record()
- archive()
- get()
- query()
- verify()
- get_health()

Dependency via shared import + protocol injection only.
"""

from typing import Any, Dict, List, Protocol


class RecorderInterface(Protocol):
    """Public interface for the Audit Recorder.

    Per ADR-004 (Failure Termination), ADR-006 (External Boundary),
    ADR-007 (Verification as State Transition).

    The Audit Recorder is the terminal unit — it receives results
    from Execution Scheduler and records them immutably. It does
    not propagate anything further. Only these six entry points
    are publicly consumable.
    """

    def record(self, execution_result: Any) -> Any:
        """Record an execution outcome as an Audit Record.

        Creates an immutable Audit Record in RECORDED state.
        Validates that all traceability references are present.

        Args:
            execution_result: Observable Outcome from Execution Scheduler.

        Returns:
            AuditRecord in RECORDED state.

        Raises:
            IncompleteRecordError: if required references are missing.
            DuplicateRecordError: if a record for this execution already exists.
        """
        ...

    def archive(self, audit_id: str) -> Any:
        """Archive an audit record.

        Moves the record to ARCHIVED (terminal) state.
        Can transition from RECORDED or VERIFIED per AUDIT_SPEC L93-L98.

        Args:
            audit_id: The audit record to archive.

        Returns:
            Archived AuditRecord.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
            ArchiveConflictError: if already archived.
        """
        ...

    def get(self, audit_id: str) -> Any:
        """Retrieve an audit record by its ID.

        Args:
            audit_id: The audit record to retrieve.

        Returns:
            AuditRecord.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
        """
        ...

    def query(
        self,
        filters: Dict[str, str] = None,
    ) -> List[Any]:
        """Query audit records by filter criteria.

        Supports filtering by: execution_reference, approval_reference,
        contract_reference, capability_reference, citizen_reference,
        outcome, and verification status.

        Args:
            filters: Dictionary of filter criteria.

        Returns:
            List of matching AuditRecord (may be empty).
        """
        ...

    def verify(self, audit_id: str) -> Any:
        """Verify an audit record's traceability.

        Per ADR-007: verification is a state transition
        Recorded → Verified within the Audit Recorder.
        Does NOT change the outcome. Only checks compliance.

        Args:
            audit_id: The audit record to verify.

        Returns:
            VerificationResult.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
            VerificationFailureError: if verification fails.
        """
        ...

    def get_health(self) -> Dict[str, Any]:
        """Return current health status.

        Returns:
            Dict with status, lifecycle, record count, and metrics.
        """
        ...
