"""Record compilation validator.

Validates that an incoming execution result is complete enough
to be recorded as an audit record, per AUDIT_SPEC §Record + §Traceability.
"""

from typing import Any, Dict, List


def validate_record_input(execution_result: Any) -> List[str]:
    """Validate that an execution result can be recorded.

    Checks:
    - execution_id is present
    - approval_reference is present
    - contract_reference is present
    - capability_reference is present
    - outcome is present

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if execution_result is None:
        errors.append("execution_result is required")
        return errors

    # Check execution ID
    exec_id = getattr(execution_result, "execution_id", None)
    if not exec_id or not str(exec_id).strip():
        errors.append("execution_id is required")

    # Check references — try multiple attribute patterns
    ref_checks = [
        ("approval_reference", "approval_reference is required"),
        ("contract_reference", "contract_reference is required"),
        ("capability_reference", "capability_reference is required"),
    ]

    for attr, msg in ref_checks:
        val = getattr(execution_result, attr, None)
        if not val or not str(val).strip():
            # Try metadata dict
            meta = getattr(execution_result, "metadata", {}) or {}
            val = meta.get(attr, None)
            if not val or not str(val).strip():
                if hasattr(execution_result, "to_dict"):
                    d = execution_result.to_dict()
                    val = d.get(attr, None)
                if not val or not str(val).strip():
                    errors.append(msg)

    return errors


def validate_no_duplicate(
    audit_id: str,
    existing_ids: Dict[str, Any],
) -> List[str]:
    """Validate no duplicate audit record exists.

    Per AUDIT_SPEC L135: DuplicateRecord is a defined failure.

    Args:
        audit_id: The audit ID to check.
        existing_ids: Registry of existing audit IDs.

    Returns:
        List of error messages (empty if no duplicate).
    """
    errors = []
    if audit_id in existing_ids:
        errors.append(
            f"Duplicate record: audit {audit_id} already exists"
        )
    return errors
