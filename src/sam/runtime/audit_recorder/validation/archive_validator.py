"""Archive validators.

Validates that an audit record can be archived per
AUDIT_SPEC §Audit Lifecycle.

Legal transitions: Recorded → Archived, Verified → Archived
Archived is terminal.
"""

from typing import Any, List

from ..state.audit_state import AuditRecordState


def validate_archive_eligibility(record: Any) -> List[str]:
    """Validate that a record is eligible for archiving.

    Checks:
    - Record exists
    - Record is not already archived (terminal)
    - Record is in RECORDED or VERIFIED state

    Per AUDIT_SPEC L93-L98: Archived is terminal.
    Only RECORDED and VERIFIED can transition to ARCHIVED.

    Args:
        record: The AuditRecord to check.

    Returns:
        List of error messages (empty if eligible).
    """
    errors = []

    if record is None:
        errors.append("record is required for archive")
        return errors

    state = getattr(record, "_state", None)

    if state == AuditRecordState.ARCHIVED:
        errors.append(
            "Cannot archive already-archived record — "
            "Archived is terminal (AUDIT_SPEC L98)"
        )
        return errors

    if state not in (AuditRecordState.RECORDED, AuditRecordState.VERIFIED):
        state_str = str(state) if state else "None"
        errors.append(
            f"Cannot archive record in state {state_str}. "
            f"Must be RECORDED or VERIFIED."
        )

    return errors


def validate_archive_completeness(record: Any) -> List[str]:
    """Validate that the record data is complete before archiving.

    Archived records must have all required data because
    they cannot be modified afterward.

    Args:
        record: The AuditRecord to check.

    Returns:
        List of error messages (empty if complete).
    """
    errors = []

    if record is None:
        return errors

    # Check identity
    identity = getattr(record, "identity", None)
    if identity is None:
        errors.append("Cannot archive: record has no identity")
        return errors

    # Check outcome
    outcome = getattr(record, "outcome", None)
    if not outcome or not str(outcome).strip():
        errors.append("Cannot archive: record has no outcome")

    return errors
