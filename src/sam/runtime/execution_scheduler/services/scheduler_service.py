"""Scheduler Service — Main orchestrator for Execution Scheduler.

Implements 6 public methods: create_execution, schedule, transition,
verify, get, get_health.

ADR-005: Strict Linear Ordering — Approval-arrival order.
ADR-003: Idempotency — Contract declares, Execution observes.
ADR-004: Linear failure propagation — no feedback, no retry.
"""

from typing import Any, Dict, Optional
import uuid

from src.sam.runtime.contracts import ContractIdempotency
from src.sam.runtime.execution_scheduler.lifecycle.scheduler_lifecycle import (
    SchedulerLifecycle,
    SchedulerLifecycleState,
)
from src.sam.runtime.execution_scheduler.models.execution_identity import (
    ExecutionIdentity,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
    ExecutionResultState,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
    ExecutionLifecycleState,
)
from src.sam.runtime.execution_scheduler.services.health_service import (
    HealthService,
)
from src.sam.runtime.execution_scheduler.validation.approval_validator import (
    ApprovalValidator,
)
from src.sam.runtime.execution_scheduler.validation.ordering_validator import (
    OrderingValidator,
)
from src.sam.runtime.execution_scheduler.validation.idempotency_validator import (
    IdempotencyValidator,
)
from src.sam.runtime.execution_scheduler.validation.lifecycle_validator import (
    LifecycleValidator,
)
from src.sam.runtime.execution_scheduler.validation.verification_validator import (
    VerificationValidator,
)
from src.sam.runtime.execution_scheduler.validation.boundary_validator import (
    BoundaryValidator,
)
from src.sam.runtime.execution_scheduler.validation.invariant_validator import (
    InvariantValidator,
)
from src.sam.runtime.execution_scheduler.exceptions.execution_errors import (
    ExecutionNotFoundError,
    InvalidTransitionError,
    OrderingViolationError,
    InvalidApprovalError,
    ExecutionConflictError,
    MissingContractError,
    NotOperationalError,
    InvalidExecutionRequestError,
    VerificationFailureError,
    MissingApprovalError,
)


class SchedulerService:
    """Execution Scheduler — coordinates execution of approved operations.

    Lifecycle: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED

    Dependency via public contract injection (Protocols only):
    - Approval Coordinator: validates approval state
    - Contract Enforcer: reads idempotency declaration
    - Discovery Resolver: verifies capability reference

    Not imported from: AC, CE, DR, CM, CH, AR, registry, internal
    """

    def __init__(self):
        self._lifecycle = SchedulerLifecycle()
        self._health = HealthService(self._lifecycle)
        self._records: Dict[str, ExecutionStateRecord] = {}
        self._sequence_counter: int = 0

    # ──────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────

    def initialize(self) -> None:
        """Initialize the scheduler."""
        self._lifecycle.transition(SchedulerLifecycleState.INITIALIZING)
        self._lifecycle.transition(SchedulerLifecycleState.RUNNING)

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._lifecycle.transition(SchedulerLifecycleState.STOPPING)
        self._lifecycle.transition(SchedulerLifecycleState.STOPPED)

    def _require_operational(self) -> None:
        """Guard: raise if not operational."""
        if not self._lifecycle.is_operational():
            raise NotOperationalError(
                f"Scheduler is not operational "
                f"(state={self._lifecycle.state.value})"
            )

    # ──────────────────────────────────────────────
    # Public API: create_execution
    # ──────────────────────────────────────────────

    def create_execution(
        self,
        request: ExecutionRequest,
        approval_state: Any = None,
        contract_idempotency: str = ContractIdempotency.NON_IDEMPOTENT.value,
    ) -> ExecutionIdentity:
        """Create a new Execution from an approved request.

        Gates:
        1. Request validation — all required fields present.
        2. Approval validation — must be Approved.
        3. Idempotency observation — ADR-003 check.
        4. Execution identity creation.

        Args:
            request: The ExecutionRequest.
            approval_state: Current state of referenced Approval.
            contract_idempotency: Idempotency declaration from Contract.

        Returns:
            ExecutionIdentity for the created execution.

        Raises:
            InvalidExecutionRequestError: if request is invalid.
            InvalidApprovalError: if approval is not Approved.
            ExecutionConflictError: if non-idempotent re-execution.
        """
        self._require_operational()

        # 1. Validate request structure
        try:
            request.validate()
        except ValueError as e:
            raise InvalidExecutionRequestError(str(e))

        # 2. Validate approval is Approved
        if approval_state is not None:
            if not ApprovalValidator.validate_approved(approval_state):
                raise InvalidApprovalError(
                    f"Approval must be in APPROVED state, "
                    f"got '{approval_state}'"
                )

        # 3. Idempotency observation (ADR-003)
        try:
            idemp = ContractIdempotency(contract_idempotency)
        except ValueError:
            idemp = ContractIdempotency.NON_IDEMPOTENT

        try:
            IdempotencyValidator.check_repeat_allowed(
                approval_ref=request.approval_reference,
                contract_ref=request.contract_reference,
                capability_ref=request.capability_reference,
                records=self._records,
                contract_idempotency=idemp,
            )
        except ValueError as e:
            raise ExecutionConflictError(str(e))

        # 4. Create execution identity
        execution_id = str(uuid.uuid4())
        identity = ExecutionIdentity(
            execution_id=execution_id,
            approval_reference=request.approval_reference,
            contract_reference=request.contract_reference,
            capability_reference=request.capability_reference,
        )
        identity.validate()

        # 5. Assign sequence number (ordering)
        self._sequence_counter += 1
        seq = self._sequence_counter

        # 6. Create and register state record
        record = ExecutionStateRecord(
            identity=identity,
            request=request,
            lifecycle_state=ExecutionLifecycleState.CREATED,
            sequence_number=seq,
        )
        self._records[execution_id] = record

        return identity

    # ──────────────────────────────────────────────
    # Public API: schedule
    # ──────────────────────────────────────────────

    def schedule(self, execution_id: str) -> None:
        """Schedule an execution for processing.

        Enforces ADR-005 Strict Linear Ordering:
        - Approval-arrival order = Execution order.
        - No bypass — earlier sequences must complete first.

        Transitions from CREATED to QUEUED.

        Args:
            execution_id: The execution to schedule.

        Raises:
            ExecutionNotFoundError: if execution_id not found.
            OrderingViolationError: if ordering constraint violated.
        """
        self._require_operational()

        record = self._get_record(execution_id)

        # Enforce ordering
        all_records = list(self._records.values())
        try:
            OrderingValidator.validate_order(record, all_records)
        except ValueError as e:
            raise OrderingViolationError(str(e))

        # Transition to QUEUED
        self._transition_record(record, ExecutionLifecycleState.QUEUED)

    # ──────────────────────────────────────────────
    # Public API: transition
    # ──────────────────────────────────────────────

    def transition(self, execution_id: str, new_state: str) -> None:
        """Transition an execution to a new lifecycle state.

        Legal transitions per EXECUTION_SPEC L135-L148.

        Args:
            execution_id: The execution to transition.
            new_state: Target lifecycle state name (string).

        Raises:
            ExecutionNotFoundError: if execution_id not found.
            InvalidTransitionError: if transition is illegal.
        """
        self._require_operational()

        record = self._get_record(execution_id)

        try:
            target = ExecutionLifecycleState(new_state.upper())
        except ValueError:
            raise InvalidTransitionError(
                f"Unknown lifecycle state: '{new_state}'"
            )

        try:
            self._transition_record(record, target)
        except ValueError as e:
            raise InvalidTransitionError(str(e))

    # ──────────────────────────────────────────────
    # Public API: verify
    # ──────────────────────────────────────────────

    def verify(self, execution_id: str) -> Dict[str, Any]:
        """Trigger verification of an execution's preconditions.

        Verifies: approval valid, contract intact, capability valid.

        Args:
            execution_id: The execution to verify.

        Returns:
            Dict with verification results.

        Raises:
            ExecutionNotFoundError: if execution_id not found.
            VerificationFailureError: if verification fails.
        """
        self._require_operational()

        record = self._get_record(execution_id)

        try:
            result = VerificationValidator.verify_preconditions(
                approval_ref=record.identity.approval_reference,
                contract_ref=record.identity.contract_reference,
                capability_ref=record.identity.capability_reference,
            )
        except ValueError as e:
            raise VerificationFailureError(str(e))

        record.metadata["verified"] = result["verified"]
        record.metadata["verification_timestamp"] = str(uuid.uuid4())
        return result

    # ──────────────────────────────────────────────
    # Public API: get
    # ──────────────────────────────────────────────

    def get(self, execution_id: str) -> ExecutionStateRecord:
        """Retrieve an execution by its ID.

        Args:
            execution_id: The execution to retrieve.

        Returns:
            ExecutionStateRecord for the execution.

        Raises:
            ExecutionNotFoundError: if execution_id not found.
        """
        return self._get_record(execution_id)

    # ──────────────────────────────────────────────
    # Public API: get_health
    # ──────────────────────────────────────────────

    def get_health(self) -> Dict[str, Any]:
        """Return current health status of the scheduler."""
        return self._health.get_health()

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    def _get_record(self, execution_id: str) -> ExecutionStateRecord:
        """Get a record by execution_id or raise.

        Args:
            execution_id: The execution ID to look up.

        Returns:
            The ExecutionStateRecord.

        Raises:
            ExecutionNotFoundError: if execution_id not found.
        """
        if execution_id not in self._records:
            raise ExecutionNotFoundError(
                f"Execution '{execution_id}' not found"
            )
        return self._records[execution_id]

    def _transition_record(
        self,
        record: ExecutionStateRecord,
        target: ExecutionLifecycleState,
    ) -> None:
        """Transition a record, wrapping ValueError to InvalidTransitionError.

        Args:
            record: The execution record.
            target: Target lifecycle state.

        Raises:
            InvalidTransitionError: if transition is illegal.
        """
        try:
            LifecycleValidator.validate_transition(record, target)
        except ValueError as e:
            raise InvalidTransitionError(str(e))

        if target in {
            ExecutionLifecycleState.COMPLETED,
            ExecutionLifecycleState.FAILED,
            ExecutionLifecycleState.CANCELLED,
            ExecutionLifecycleState.TIMED_OUT,
        }:
            result_state_map = {
                ExecutionLifecycleState.COMPLETED: ExecutionResultState.COMPLETED,
                ExecutionLifecycleState.FAILED: ExecutionResultState.FAILED,
                ExecutionLifecycleState.CANCELLED: ExecutionResultState.CANCELLED,
                ExecutionLifecycleState.TIMED_OUT: ExecutionResultState.TIMED_OUT,
            }
            result = ExecutionResult(
                execution_id=record.identity.execution_id,
                state=result_state_map[target],
                message=f"Execution reached state {target.value}",
            )
            record.set_result(result)

        record.transition(target)

    # ──────────────────────────────────────────────
    # Testing / introspection helpers
    # ──────────────────────────────────────────────

    @property
    def record_count(self) -> int:
        """Return number of tracked executions."""
        return len(self._records)

    @property
    def lifecycle_state(self) -> SchedulerLifecycleState:
        """Return current scheduler lifecycle state."""
        return self._lifecycle.state

    def list_executions(self):
        """Return all execution records (for testing)."""
        return list(self._records.values())

    def list_executions_by_sequence(self):
        """Return executions sorted by sequence number."""
        return sorted(
            self._records.values(),
            key=lambda r: r.sequence_number,
        )
