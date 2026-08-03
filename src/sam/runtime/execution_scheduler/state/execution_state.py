"""Execution Lifecycle State — EXECUTION_SPEC §Execution Lifecycle.

8 lifecycle states: CREATED, QUEUED, RUNNING, COMPLETED, FAILED,
CANCELLED, TIMED_OUT, ARCHIVED.

Legal transitions per EXECUTION_SPEC L135-L148.
ARCHIVED is terminal.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from src.sam.runtime.execution_scheduler.models.execution_identity import (
    ExecutionIdentity,
)
from src.sam.runtime.execution_scheduler.models.execution_request import (
    ExecutionRequest,
)
from src.sam.runtime.execution_scheduler.models.execution_result import (
    ExecutionResult,
)


class ExecutionLifecycleState(str, Enum):
    """8 lifecycle states per EXECUTION_SPEC L128-L148.

    Combined from spec: Created, Queued, Running, Completed, Failed,
    Cancelled, Archived (7 listed) + TimedOut (from legal transition).
    Total: 8 states.
    """
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    ARCHIVED = "ARCHIVED"


# Legal transitions per EXECUTION_SPEC L135-L148
LEGAL_TRANSITIONS = {
    ExecutionLifecycleState.CREATED: {
        ExecutionLifecycleState.QUEUED,
        ExecutionLifecycleState.CANCELLED,
    },
    ExecutionLifecycleState.QUEUED: {
        ExecutionLifecycleState.RUNNING,
        ExecutionLifecycleState.CANCELLED,
    },
    ExecutionLifecycleState.RUNNING: {
        ExecutionLifecycleState.COMPLETED,
        ExecutionLifecycleState.FAILED,
        ExecutionLifecycleState.CANCELLED,
        ExecutionLifecycleState.TIMED_OUT,
    },
    ExecutionLifecycleState.COMPLETED: {
        ExecutionLifecycleState.ARCHIVED,
    },
    ExecutionLifecycleState.FAILED: {
        ExecutionLifecycleState.ARCHIVED,
    },
    ExecutionLifecycleState.CANCELLED: {
        ExecutionLifecycleState.ARCHIVED,
    },
    ExecutionLifecycleState.TIMED_OUT: {
        ExecutionLifecycleState.ARCHIVED,
    },
    ExecutionLifecycleState.ARCHIVED: set(),
}

# States that are considered terminal (no further transitions)
TERMINAL_STATES = {ExecutionLifecycleState.ARCHIVED}

# States where the result is "final" (execution has finished running)
RESULT_STATES = {
    ExecutionLifecycleState.COMPLETED,
    ExecutionLifecycleState.FAILED,
    ExecutionLifecycleState.CANCELLED,
    ExecutionLifecycleState.TIMED_OUT,
}


def is_valid_transition(
    current: ExecutionLifecycleState,
    target: ExecutionLifecycleState,
) -> bool:
    """Check if a transition from current to target is legal.

    Same-state is always legal (no-op).

    Args:
        current: Current lifecycle state.
        target: Target lifecycle state.

    Returns:
        True if transition is legal.
    """
    if current == target:
        return True
    allowed = LEGAL_TRANSITIONS.get(current, set())
    return target in allowed


def is_terminal_state(state: ExecutionLifecycleState) -> bool:
    """Check if state is terminal."""
    return state in TERMINAL_STATES


def is_result_state(state: ExecutionLifecycleState) -> bool:
    """Check if state represents a completed/terminal result."""
    return state in RESULT_STATES


@dataclass
class ExecutionStateRecord:
    """Mutable record representing an Execution in the scheduler.

    Tracks identity, lifecycle, result, and metadata.
    Lifecycle state is observable per EXECUTION_SPEC L120.
    """
    identity: ExecutionIdentity
    request: ExecutionRequest
    lifecycle_state: ExecutionLifecycleState = ExecutionLifecycleState.CREATED
    result: Optional[ExecutionResult] = None
    sequence_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def transition(self, target: ExecutionLifecycleState) -> None:
        """Transition to a new lifecycle state.

        Raises:
            ValueError: if the transition is illegal.
        """
        if not is_valid_transition(self.lifecycle_state, target):
            raise ValueError(
                f"Invalid transition: {self.lifecycle_state.value} "
                f"-> {target.value}"
            )
        self.lifecycle_state = target

    def set_result(self, result: ExecutionResult) -> None:
        """Attach a result to this execution record."""
        self.result = result

    def is_terminal(self) -> bool:
        """Check if this execution has reached a terminal state."""
        return is_terminal_state(self.lifecycle_state)

    def has_result(self) -> bool:
        """Check if this execution has produced a result."""
        return self.lifecycle_state in RESULT_STATES and self.result is not None

    def to_dict(self) -> Dict[str, Any]:
        """Return record as dictionary for observability."""
        d = {
            "execution_id": self.identity.execution_id,
            "lifecycle_state": self.lifecycle_state.value,
            "sequence_number": self.sequence_number,
            "terminal": self.is_terminal(),
            "identity": self.identity.to_dict(),
            "metadata": dict(self.metadata),
        }
        if self.result:
            d["result"] = self.result.state.value
            d["result_message"] = self.result.message
        return d

    def __repr__(self) -> str:
        result_str = self.result.state.value if self.result else "none"
        return (
            f"ExecutionStateRecord("
            f"id='{self.identity.execution_id}', "
            f"state={self.lifecycle_state.value}, "
            f"seq={self.sequence_number}, "
            f"result={result_str})"
        )
