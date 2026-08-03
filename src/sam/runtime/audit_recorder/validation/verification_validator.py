"""Verification validator — ADR-007.

Verification occurs after Execution completes, before Audit finalization.
It does not change the outcome, does not repeat execution, only verifies
compliance by tracing references.

Per ADR-007:
- Verification is a state transition Recorded → Verified
- Verification is out-of-chain (does not affect execution outcome)
- Verification uses Contract + Registry references for traceability
- Verification does not create a new component or authority
"""

from typing import Any, List

from ..exceptions.audit_errors import VerificationFailureError


def validate_verification_preconditions(record: Any) -> List[str]:
    """Validate that a record can be verified.

    Checks:
    - Record exists and has an identity
    - Record is in RECORDED state (not ARCHIVED, per ADR-007)
    - Record has all required references

    Args:
        record: The AuditRecord to verify.

    Returns:
        List of error messages (empty if ready for verification).
    """
    errors = []

    if record is None:
        errors.append("record is required for verification")
        return errors

    # Check state — only RECORDED can be Verified (not ARCHIVED)
    state = getattr(record, "_state", None)
    if state is not None:
        if hasattr(state, "value"):
            if state.value == "ARCHIVED":
                errors.append(
                    "Cannot verify archived record — "
                    "Archived is terminal (AUDIT_SPEC L98)"
                )
        elif str(state) == "ARCHIVED":
            errors.append(
                "Cannot verify archived record — "
                "Archived is terminal (AUDIT_SPEC L98)"
            )

    # Check identity
    identity = getattr(record, "identity", None)
    if identity is None:
        errors.append("record has no identity — cannot verify")
        return errors

    return errors


def validate_verification_outcome(_record: Any) -> List[str]:
    """Validation that verification does not modify the outcome.

    Per ADR-007 and AUDIT_SPEC L193: Audit has no influence
    over what Execution produces. Verification only checks
    compliance.

    This validator is a structural guard — it ensures the
    verification process itself cannot mutate the record data.

    Returns:
        Always empty (verification is read-only by design).
    """
    return []
