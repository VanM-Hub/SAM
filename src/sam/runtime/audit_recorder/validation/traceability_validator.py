"""Traceability validators.

Ensures the audit record's traceability chain is complete
per AUDIT_SPEC §Traceability Rules. Every record must
reference Execution, Approval, Contract, Capability, and Citizen.
"""

from typing import Any, Dict, List


# Required reference fields per AUDIT_SPEC L106-L115
REQUIRED_REFERENCES = [
    "execution_reference",
    "approval_reference",
    "contract_reference",
    "capability_reference",
    "citizen_reference",
]


def validate_traceability(record: Any) -> List[str]:
    """Validate that all traceability references are present and non-empty.

    Per AUDIT_SPEC L106-L115: each record must be traceable back
    through the entire chain: Audit ← Execution ← Approval ←
    Contract ← Capability ← Citizen.

    Args:
        record: An AuditRecord or similar object with identity.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if record is None:
        errors.append("record is required")
        return errors

    identity = getattr(record, "identity", None)
    if identity is None:
        errors.append("record has no identity — cannot verify traceability")
        return errors

    for ref_field in REQUIRED_REFERENCES:
        val = getattr(identity, ref_field, None)
        if not val or not str(val).strip():
            errors.append(f"Missing reference: {ref_field}")

    return errors


def validate_traceability_chain(
    record: Any,
    reference_map: Dict[str, Any] = None,
) -> List[str]:
    """Validate that referenced objects exist in the reference map.

    Args:
        record: An AuditRecord with identity.
        reference_map: Dict mapping reference IDs to objects.
                       If None, only checks presence (not existence).

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if record is None:
        errors.append("record is required")
        return errors

    identity = getattr(record, "identity", None)
    if identity is None:
        return errors  # Already caught by validate_traceability

    if reference_map is None:
        return errors  # Skip existence check if no reference map provided
    if not reference_map:
        return errors  # Empty map = no references registered yet, skip existence check

    for ref_field in REQUIRED_REFERENCES:
        val = getattr(identity, ref_field, None)
        if val and val.strip():
            if val not in reference_map:
                errors.append(
                    f"Broken traceability: {ref_field} "
                    f"'{val}' not found in reference map"
                )

    return errors
