"""ExecutionSchedulerInterface — Public API Protocol.

6 public methods per I0-001 §2.6:
- create_execution()
- schedule()
- transition()
- verify()
- get()
- get_health()

Dependency via public contract injection only.
"""

from typing import Protocol, Dict, Any


class ExecutionSchedulerInterface(Protocol):
    """Public interface for the Execution Scheduler.

    Per ADR-005 (Strict Linear Ordering), ADR-003 (Idempotency Observation),
    ADR-004 (Linear Failure Propagation).

    Only these six entry points are publicly consumable.
    """

    def create_execution(self, request: Any) -> Any:
        """Create an Execution from an approved request.

        Validates: Approval is Approved, Contract is valid,
        Capability is resolved. Observes idempotency declaration
        from Contract (ADR-003).

        Args:
            request: ExecutionRequest with approval/contract/capability refs.

        Returns:
            ExecutionIdentity of the created execution.

        Raises:
            InvalidApprovalError: if Approval is not Approved.
            ExecutionConflictError: if operation non-idempotent and already Completed.
            MissingContractError: if contract reference is invalid.
        """
        ...

    def schedule(self, execution_id: str) -> None:
        """Schedule an execution for processing.

        Enforces ADR-005 Strict Linear Ordering:
        Approval-arrival order = Execution order.
        Moves execution to QUEUED state.

        Args:
            execution_id: The execution to schedule.

        Raises:
            ExecutionNotFoundError: if execution_id does not exist.
            OrderingViolationError: if ordering constraints are violated.
        """
        ...

    def transition(self, execution_id: str, new_state: str) -> None:
        """Transition an execution to a new lifecycle state.

        Legal transitions per EXECUTION_SPEC L135-L148.
        Archived is terminal.

        Args:
            execution_id: The execution to transition.
            new_state: Target lifecycle state name.

        Raises:
            InvalidTransitionError: if the transition is not legal.
            ExecutionNotFoundError: if execution_id does not exist.
        """
        ...

    def verify(self, execution_id: str) -> Dict[str, Any]:
        """Trigger verification of an execution's preconditions.

        Verifies: approval still valid, contract intact,
        capability reference valid.

        Args:
            execution_id: The execution to verify.

        Returns:
            Dict with verification results.

        Raises:
            VerificationFailureError: if verification fails.
            ExecutionNotFoundError: if execution_id does not exist.
        """
        ...

    def get(self, execution_id: str) -> Any:
        """Retrieve an execution by its ID.

        Args:
            execution_id: The execution to retrieve.

        Returns:
            ExecutionStateRecord for the execution.

        Raises:
            ExecutionNotFoundError: if execution_id does not exist.
        """
        ...

    def get_health(self) -> Dict[str, Any]:
        """Return current health status.

        Returns:
            Dict with health information.
        """
        ...
