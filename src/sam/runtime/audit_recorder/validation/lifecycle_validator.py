"""Lifecycle validators for Audit Recorder.

Validates per-unit lifecycle transitions and per-record
lifecycle legality per AUDIT_SPEC §Audit Lifecycle.
"""

from typing import Any, List

from ..lifecycle.recorder_lifecycle import (
    RecorderLifecycleState,
    is_legal_recorder_transition,
)
from ..state.audit_state import (
    AuditRecordState,
    is_legal_audit_transition,
)


def validate_recorder_lifecycle_transition(
    current: RecorderLifecycleState,
    target: RecorderLifecycleState,
) -> List[str]:
    """Validate a recorder-level lifecycle transition.

    Args:
        current: Current recorder lifecycle state.
        target: Target recorder lifecycle state.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    if current is None:
        errors.append("current state is required")
        return errors
    if target is None:
        errors.append("target state is required")
        return errors

    if not is_legal_recorder_transition(current, target):
        errors.append(
            f"Illegal recorder transition: "
            f"{current.value} -> {target.value}"
        )
    return errors


def validate_audit_record_transition(
    current_state: AuditRecordState,
    target_state: AuditRecordState,
) -> List[str]:
    """Validate an audit record lifecycle transition.

    Per AUDIT_SPEC L93-L98:
    - Recorded -> Verified
    - Recorded -> Archived
    - Verified -> Archived
    - Archived is terminal

    Args:
        current_state: Current audit record state.
        target_state: Target audit record state.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    if current_state is None:
        errors.append("current state is required")
        return errors
    if target_state is None:
        errors.append("target state is required")
        return errors

    if not is_legal_audit_transition(current_state, target_state):
        errors.append(
            f"Illegal audit record transition: "
            f"{current_state.value} -> {target_state.value}"
        )
    return errors


def validate_record_in_required_state(
    record: Any,
    required_state: AuditRecordState,
    operation: str,
) -> List[str]:
    """Validate that a record is in the required state for an operation.

    Args:
        record: The AuditRecord to check.
        required_state: The state the record must be in.
        operation: Name of the operation (for error messages).

    Returns:
        List of error messages (empty if state matches).
    """
    errors = []
    if record is None:
        errors.append(f"record is required for {operation}")
        return errors

    current_state = getattr(record, "_state", None)
    if current_state != required_state:
        current_str = str(current_state) if current_state else "None"
        errors.append(
            f"Cannot {operation}: record is in "
            f"{current_str}, must be in {required_state.value}"
        )
    return errors
