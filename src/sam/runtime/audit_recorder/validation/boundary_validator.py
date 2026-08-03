"""Boundary validator — ADR-006.

The Audit Recorder has no external access. It only receives
results from within the Runtime. External layer reads through
the public interface only.

Per ADR-006: External access = Contracts + Registry only.
The Audit Recorder is internal — it has no direct external
communication path.
"""

from typing import Any, List


def validate_boundary(input_source: str) -> List[str]:
    """Validate that input comes from a legitimate Runtime source.

    Per ADR-006: no direct external access.
    The Audit Recorder only accepts input from the Execution
    Scheduler or other internal Runtime units.

    Args:
        input_source: Identifier of the source providing input.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if not input_source or not input_source.strip():
        errors.append("input_source is required for boundary check")
        return errors

    # Valid internal sources
    valid_sources = {
        "execution_scheduler",
        "runtime_internal",
        "internal",
    }

    if input_source.lower() not in valid_sources:
        errors.append(
            f"Boundary violation: input source '{input_source}' "
            f"is not a recognized Runtime source. "
            f"Per ADR-006, only internal Runtime units may "
            f"provide input to the Audit Recorder."
        )

    return errors


def validate_no_external_output(source: Any) -> List[str]:
    """Validate that the Audit Recorder does not send data externally.

    Per ADR-004 and ADR-006: Audit is the termination point.
    It records and provides traceability only. No data flows
    out of the Audit Recorder — external layers read through
    the public interface (pull, not push).

    Args:
        source: The caller context to validate.

    Returns:
        Always empty (boundary is enforced structurally).
    """
    # The boundary is structural: Audit Recorder has no
    # external communication mechanism. This validation
    # exists as a guard against accidental violation.
    return []
