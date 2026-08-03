"""Execution errors — EXECUTION_SPEC §Failure Behaviour.

6 defined failures + Execution Conflict (ADR-003):
- Missing Approval, Invalid Approval, Missing Contract
- Capability Unavailable, Execution Timeout, Execution Failure
- Execution Conflict (ADR-003 — non-idempotent re-execution)

Plus internal errors: ExecutionNotFound, InvalidTransition,
OrderingViolation, VerificationFailure, NotOperational, InvalidRequest
"""


class ExecutionError(Exception):
    """Base exception for all execution errors.

    Authority: EXECUTION_SPEC §Failure Behaviour
    """
    pass


# ──────────────────────────────────────────────
# Defined Failures (EXECUTION_SPEC L150-L163)
# ──────────────────────────────────────────────

class MissingApprovalError(ExecutionError):
    """No Approval is referenced."""
    pass


class InvalidApprovalError(ExecutionError):
    """The referenced Approval is not valid for this operation."""
    pass


class MissingContractError(ExecutionError):
    """The referenced Contract is absent."""
    pass


class CapabilityUnavailableError(ExecutionError):
    """The Capability cannot be performed."""
    pass


class ExecutionTimeoutError(ExecutionError):
    """The operation exceeded its allowed duration."""
    pass


class ExecutionFailureError(ExecutionError):
    """The operation did not complete successfully."""
    pass


class ExecutionConflictError(ExecutionError):
    """Attempt to re-execute a non-idempotent Completed operation.

    Authority: ADR-003 L234/L308 — Operation-Defined Semantics
    """
    pass


# ──────────────────────────────────────────────
# Internal Errors
# ──────────────────────────────────────────────

class ExecutionNotFoundError(ExecutionError):
    """The requested execution ID does not exist in the registry."""
    pass


class InvalidTransitionError(ExecutionError):
    """The requested lifecycle transition is invalid."""
    pass


class OrderingViolationError(ExecutionError):
    """Strict Linear Ordering (ADR-005) was violated."""
    pass


class VerificationFailureError(ExecutionError):
    """Verification of execution preconditions failed."""
    pass


class NotOperationalError(ExecutionError):
    """Operation attempted while scheduler is not in operational state."""
    pass


class InvalidExecutionRequestError(ExecutionError):
    """The execution request failed structural validation."""
    pass
