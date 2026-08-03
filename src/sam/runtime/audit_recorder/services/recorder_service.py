"""RecorderService — the main orchestrator for Audit Recorder.

Coordinates recording, verification, archiving, and querying of
audit records. Implements RecorderInterface.

Per AUDIT_SPEC: observes and records. No influence over outcome.
Per ADR-004: terminal — records failures, does not propagate.
Per ADR-007: verification as state transition Recorded → Verified.
"""

from typing import Any, Dict, List, Optional

from ..exceptions.audit_errors import (
    ArchiveConflictError,
    AuditNotFoundError,
    BrokenTraceabilityError,
    DuplicateRecordError,
    IncompleteRecordError,
    InvalidRecordError,
    MissingReferenceError,
    VerificationFailureError,
)
from ..lifecycle.recorder_lifecycle import (
    RecorderLifecycleState,
    is_legal_recorder_transition,
)
from ..models.audit_identity import AuditIdentity
from ..models.audit_record import AuditRecord
from ..models.verification_result import (
    VerificationResult,
    VerificationStatus,
)
from ..services.health_service import HealthService
from ..state.audit_state import (
    AuditRecordState,
    is_legal_audit_transition,
)
from ..validation.archive_validator import (
    validate_archive_completeness,
    validate_archive_eligibility,
)
from ..validation.boundary_validator import validate_boundary
from ..validation.invariant_validator import validate_immutability
from ..validation.lifecycle_validator import (
    validate_audit_record_transition,
)
from ..validation.record_validator import (
    validate_no_duplicate,
    validate_record_input,
)
from ..validation.traceability_validator import (
    validate_traceability,
    validate_traceability_chain,
)
from ..validation.verification_validator import (
    validate_verification_preconditions,
)


class RecorderService:
    """Main orchestrator for Audit Recorder.

    Implements RecorderInterface: record, archive, get, query,
    verify, get_health.

    The RecorderService is the termination point of the Runtime.
    It receives Observable Outcomes from the Execution Scheduler,
    creates immutable audit records, verifies them per ADR-007,
    and archives them. Failure propagation ends here (ADR-004).
    """

    def __init__(self):
        """Initialize an empty RecorderService."""
        self._records: Dict[str, Dict[str, Any]] = {}
        self._lifecycle_state = RecorderLifecycleState.UNINITIALIZED
        self._reference_map: Dict[str, Any] = {}
        self._health_service = HealthService(
            lifecycle_getter=lambda: self._lifecycle_state,
            record_count_getter=lambda: len(self._records),
        )

    # --- Lifecycle Management ---

    def initialize(self):
        """Transition to INITIALIZING, then RUNNING."""
        self._transition_lifecycle(RecorderLifecycleState.INITIALIZING)
        self._transition_lifecycle(RecorderLifecycleState.RUNNING)

    def shutdown(self):
        """Transition through STOPPING to STOPPED."""
        if self._lifecycle_state == RecorderLifecycleState.RUNNING:
            self._transition_lifecycle(RecorderLifecycleState.STOPPING)
        if self._lifecycle_state == RecorderLifecycleState.STOPPING:
            self._transition_lifecycle(RecorderLifecycleState.STOPPED)

    def _transition_lifecycle(self, target: RecorderLifecycleState):
        """Transition the recorder to a new lifecycle state."""
        if not is_legal_recorder_transition(
            self._lifecycle_state, target
        ):
            raise ValueError(
                f"Illegal recorder transition: "
                f"{self._lifecycle_state.value} -> {target.value}"
            )
        self._lifecycle_state = target

    # --- Public API: RecorderInterface ---

    def record(
        self,
        execution_result: Any,
        input_source: str = "runtime_internal",
    ) -> AuditRecord:
        """Record an execution outcome as an immutable Audit Record.

        Per AUDIT_SPEC: records the operational event.
        Per ADR-006: validates input source is internal.

        Args:
            execution_result: Observable Outcome from Execution Scheduler.
            input_source: Source identifier (must be internal).

        Returns:
            AuditRecord in RECORDED state.

        Raises:
            IncompleteRecordError: if required references are missing.
            DuplicateRecordError: if a record for this execution already exists.
            InvalidRecordError: if the record is malformed.
        """
        # Boundary check (ADR-006)
        boundary_errors = validate_boundary(input_source)
        if boundary_errors:
            raise InvalidRecordError("; ".join(boundary_errors))

        # Validate record input
        input_errors = validate_record_input(execution_result)
        if input_errors:
            raise IncompleteRecordError("; ".join(input_errors))

        # Extract execution ID for duplicate check
        exec_id = getattr(execution_result, "execution_id", "")
        audit_id = f"audit-{exec_id}" if exec_id else "audit-unknown"

        # Check for duplicate
        dup_errors = validate_no_duplicate(audit_id, self._records)
        if dup_errors:
            raise DuplicateRecordError("; ".join(dup_errors))

        # Build audit identity from execution result
        identity = self._build_identity_from_result(
            execution_result, audit_id
        )

        # Determine outcome
        outcome = self._extract_outcome(execution_result)
        outcome_message = getattr(execution_result, "message", "") or ""

        # Create immutable audit record
        record = AuditRecord(
            identity=identity,
            outcome=outcome,
            outcome_message=outcome_message,
            context={
                "input_source": input_source,
                "execution_id": exec_id,
            },
        )

        # Store with internal state tracking
        self._records[audit_id] = {
            "record": record,
            "_state": AuditRecordState.RECORDED,
        }

        return record

    def archive(self, audit_id: str) -> AuditRecord:
        """Archive an audit record (terminal).

        Per AUDIT_SPEC L93-L98: can transition from RECORDED
        or VERIFIED to ARCHIVED. Archived is terminal.

        Args:
            audit_id: The audit record to archive.

        Returns:
            AuditRecord with ARCHIVED state marker.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
            ArchiveConflictError: if already archived.
        """
        entry = self._records.get(audit_id)
        if entry is None:
            raise AuditNotFoundError(
                f"Audit record '{audit_id}' not found"
            )

        current_state = entry["_state"]

        # Validate eligibility
        errors = validate_archive_eligibility(
            self._wrap_with_state(entry["record"], current_state)
        )
        if errors:
            raise ArchiveConflictError("; ".join(errors))

        # Validate completeness
        comp_errors = validate_archive_completeness(entry["record"])
        if comp_errors:
            raise IncompleteRecordError("; ".join(comp_errors))

        # Transition to ARCHIVED
        target = AuditRecordState.ARCHIVED
        trans_errors = validate_audit_record_transition(
            current_state, target
        )
        if trans_errors:
            raise ArchiveConflictError("; ".join(trans_errors))

        entry["_state"] = target
        return entry["record"]

    def get(self, audit_id: str) -> AuditRecord:
        """Retrieve an audit record by its ID.

        Args:
            audit_id: The audit record to retrieve.

        Returns:
            AuditRecord.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
        """
        entry = self._records.get(audit_id)
        if entry is None:
            raise AuditNotFoundError(
                f"Audit record '{audit_id}' not found"
            )
        return entry["record"]

    def query(
        self,
        filters: Dict[str, str] = None,
    ) -> List[AuditRecord]:
        """Query audit records by filter criteria.

        Args:
            filters: Dictionary of filter criteria. Supported keys:
                - execution_reference
                - approval_reference
                - contract_reference
                - capability_reference
                - citizen_reference
                - outcome
                - verification_status
                - audit_id

        Returns:
            List of matching AuditRecord (may be empty).
        """
        if filters is None or len(filters) == 0:
            # Return all records
            return [
                entry["record"]
                for entry in self._records.values()
            ]

        results = []
        for entry in self._records.values():
            record = entry["record"]
            if self._matches_filters(record, entry, filters):
                results.append(record)

        return results

    def verify(self, audit_id: str) -> VerificationResult:
        """Verify an audit record's traceability.

        Per ADR-007: verification is a state transition
        Recorded → Verified within the Audit Recorder.

        Does NOT change the outcome. Only checks compliance
        by tracing references through the chain.

        Args:
            audit_id: The audit record to verify.

        Returns:
            VerificationResult.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
            VerificationFailureError: if verification fails.
        """
        entry = self._records.get(audit_id)
        if entry is None:
            raise AuditNotFoundError(
                f"Audit record '{audit_id}' not found"
            )

        current_state = entry["_state"]
        record = entry["record"]

        # Validate preconditions
        pre_errors = validate_verification_preconditions(
            self._wrap_with_state(record, current_state)
        )
        if pre_errors:
            raise VerificationFailureError("; ".join(pre_errors))

        # Check archived — cannot verify archived records
        if current_state == AuditRecordState.ARCHIVED:
            raise VerificationFailureError(
                "Cannot verify: record is ARCHIVED (terminal)"
            )

        # Verify traceability
        trace_errors = validate_traceability(record)
        trace_chain_errors = validate_traceability_chain(
            record, self._reference_map
        )

        all_errors = trace_errors + trace_chain_errors

        if all_errors:
            # Verification failed — provides evidence
            result = VerificationResult.not_verified(
                evidence="; ".join(all_errors),
                broken_references={
                    "traceability": "; ".join(all_errors),
                },
            )
        else:
            # Verification passed
            result = VerificationResult.verified(
                evidence="All traceability references intact"
            )
            # Transition to VERIFIED (ADR-007)
            if current_state == AuditRecordState.RECORDED:
                trans_errors = validate_audit_record_transition(
                    current_state, AuditRecordState.VERIFIED
                )
                if not trans_errors:
                    entry["_state"] = AuditRecordState.VERIFIED

        return result

    def get_health(self) -> Dict[str, Any]:
        """Return current health status.

        Returns:
            Dict with status, lifecycle, record_count, and metrics.
        """
        health = self._health_service.get_health()
        health.update({
            "archived_count": sum(
                1 for e in self._records.values()
                if e["_state"] == AuditRecordState.ARCHIVED
            ),
            "verified_count": sum(
                1 for e in self._records.values()
                if e["_state"] == AuditRecordState.VERIFIED
            ),
            "recorded_count": sum(
                1 for e in self._records.values()
                if e["_state"] == AuditRecordState.RECORDED
            ),
        })
        return health

    # --- Internal helpers ---

    def _build_identity_from_result(
        self,
        execution_result: Any,
        audit_id: str,
    ) -> AuditIdentity:
        """Build an AuditIdentity from an execution result.

        Extracts references from the execution result's metadata,
        attributes, or to_dict() representation.
        """
        import datetime
        
        def _now():
            return datetime.datetime.utcnow().isoformat()

        meta = getattr(execution_result, "metadata", {}) or {}

        def _extract(key: str, default: str = "") -> str:
            val = getattr(execution_result, key, None)
            if val and str(val).strip():
                return str(val)
            val = meta.get(key, None)
            if val and str(val).strip():
                return str(val)
            if hasattr(execution_result, "to_dict"):
                d = execution_result.to_dict()
                val = d.get(key, None)
                if val and str(val).strip():
                    return str(val)
            return default

        return AuditIdentity(
            audit_id=audit_id,
            execution_reference=_extract("execution_id", "unknown"),
            approval_reference=_extract("approval_reference", "unknown"),
            contract_reference=_extract("contract_reference", "unknown"),
            capability_reference=_extract("capability_reference", "unknown"),
            citizen_reference=_extract("citizen_reference", "unknown"),
            timestamp=_now(),
        )

    @staticmethod
    def _extract_outcome(execution_result: Any) -> str:
        """Extract the outcome string from an execution result."""
        state = getattr(execution_result, "state", None)
        if state is not None:
            if hasattr(state, "value"):
                return state.value
            return str(state)
        # Try metadata
        meta = getattr(execution_result, "metadata", {}) or {}
        return meta.get("outcome", str(state) if state else "UNKNOWN")

    @staticmethod
    def _wrap_with_state(record: AuditRecord, state: AuditRecordState) -> Any:
        """Wrap a record with internal state for validation.

        Returns an object with _state attribute for validators
        that check record state.
        """
        class StateWrapper:
            def __init__(self, r, s):
                self.identity = r.identity
                self.outcome = r.outcome
                self.outcome_message = r.outcome_message
                self.verification = r.verification
                self._state = s

        return StateWrapper(record, state)

    @staticmethod
    def _matches_filters(
        record: AuditRecord,
        entry: Dict[str, Any],
        filters: Dict[str, str],
    ) -> bool:
        """Check if a record matches the given filters."""
        for key, value in filters.items():
            if key == "audit_id":
                if record.audit_id != value:
                    return False
            elif key == "execution_reference":
                if record.execution_reference != value:
                    return False
            elif key == "approval_reference":
                if record.approval_reference != value:
                    return False
            elif key == "contract_reference":
                if record.contract_reference != value:
                    return False
            elif key == "capability_reference":
                if record.capability_reference != value:
                    return False
            elif key == "citizen_reference":
                if record.citizen_reference != value:
                    return False
            elif key == "outcome":
                if record.outcome != value:
                    return False
            elif key == "verification_status":
                state = entry.get("_state")
                if state is not None:
                    if value == "VERIFIED" and state != AuditRecordState.VERIFIED:
                        return False
                    if value == "RECORDED" and state != AuditRecordState.RECORDED:
                        return False
                    if value == "ARCHIVED" and state != AuditRecordState.ARCHIVED:
                        return False
            elif key == "failure_event":
                if record.failure_event != value:
                    return False
        return True

    def set_reference_map(self, reference_map: Dict[str, Any]):
        """Set the reference map for traceability chain validation.

        Args:
            reference_map: Dict mapping reference IDs to objects.
        """
        self._reference_map = reference_map or {}

    @property
    def lifecycle_state(self) -> RecorderLifecycleState:
        """Current recorder lifecycle state."""
        return self._lifecycle_state

    @property
    def record_count(self) -> int:
        """Total number of stored audit records."""
        return len(self._records)

    def get_record_state(self, audit_id: str) -> AuditRecordState:
        """Get the lifecycle state of a specific audit record.

        Args:
            audit_id: The audit record ID.

        Returns:
            AuditRecordState of the record.

        Raises:
            AuditNotFoundError: if audit_id does not exist.
        """
        entry = self._records.get(audit_id)
        if entry is None:
            raise AuditNotFoundError(
                f"Audit record '{audit_id}' not found"
            )
        return entry["_state"]

    def get_state_counts(self) -> Dict[str, int]:
        """Get counts of records per state.

        Returns:
            Dict with state_name: count.
        """
        counts = {s.value: 0 for s in AuditRecordState}
        for entry in self._records.values():
            state = entry["_state"]
            counts[state.value] = counts.get(state.value, 0) + 1
        return counts
