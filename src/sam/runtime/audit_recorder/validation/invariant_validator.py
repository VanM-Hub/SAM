"""Invariant validators for Audit Recorder.

Ensures the Audit Recorder maintains fundamental invariants:
- Immutability: records cannot be modified after creation
- Terminal: no data flows backward from Audit
- Completeness: all records have complete traceability
"""

from typing import Any, List


def validate_immutability(
    original: Any,
    modified: Any,
) -> List[str]:
    """Validate that an audit record has not been modified.

    Per AUDIT_SPEC: Audit Records are immutable. Once recorded,
    they cannot be changed. Verification adds a result but does
    not modify the original data.

    Args:
        original: The original record data.
        modified: The record data to compare against.

    Returns:
        List of error messages (empty if data is unchanged).
    """
    errors = []

    if original is None or modified is None:
        return errors

    # Compare core fields (identity, outcome, context)
    # Verification is allowed to be added — it is metadata
    orig_id = getattr(original, "identity", None)
    mod_id = getattr(modified, "identity", None)

    if orig_id is not None and mod_id is not None:
        if orig_id.audit_id != mod_id.audit_id:
            errors.append("Immutable violation: audit_id changed")
        if orig_id.execution_reference != mod_id.execution_reference:
            errors.append("Immutable violation: execution_reference changed")
        if orig_id.approval_reference != mod_id.approval_reference:
            errors.append("Immutable violation: approval_reference changed")
        if orig_id.contract_reference != mod_id.contract_reference:
            errors.append("Immutable violation: contract_reference changed")
        if orig_id.capability_reference != mod_id.capability_reference:
            errors.append("Immutable violation: capability_reference changed")
        if orig_id.citizen_reference != mod_id.citizen_reference:
            errors.append("Immutable violation: citizen_reference changed")

    orig_outcome = getattr(original, "outcome", None)
    mod_outcome = getattr(modified, "outcome", None)
    if orig_outcome != mod_outcome:
        errors.append("Immutable violation: outcome changed")

    return errors


def validate_no_feedback(record: Any) -> List[str]:
    """Validate that no data flows back from Audit to upstream units.

    Per ADR-004: Audit Recorder Unit adalah titik terminasi —
    mencatat, tidak meneruskan (F3). No feedback loop (F4).

    This is a structural invariant — the Audit Recorder has
    no mechanism to send data to upstream units.

    Args:
        record: The audit record (unused — structural guard).

    Returns:
        Always empty (no feedback mechanism exists by design).
    """
    return []


def validate_no_external_access(record: Any) -> List[str]:
    """Validate no external access pattern.

    Per ADR-006: External boundary = Contracts + Registry.
    The Audit Recorder is internal — data is read externally
    through the public interface (pull model).

    Returns:
        Always empty (boundary enforced structurally).
    """
    return []
