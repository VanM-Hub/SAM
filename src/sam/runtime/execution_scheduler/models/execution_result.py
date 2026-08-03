"""Execution Result model — EXECUTION_SPEC §Execution Result.

Result states: Completed, Failed, Cancelled, Timed Out.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class ExecutionResultState(str, Enum):
    """Result states per EXECUTION_SPEC L106-L114."""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable execution result.

    Authority: EXECUTION_SPEC L106-L114
    """
    execution_id: str
    state: ExecutionResultState
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def completed(cls, execution_id: str, message: str = "",
                  metadata: Dict[str, Any] = None) -> "ExecutionResult":
        """Factory for COMPLETED result."""
        return cls(
            execution_id=execution_id,
            state=ExecutionResultState.COMPLETED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def failed(cls, execution_id: str, message: str = "",
               metadata: Dict[str, Any] = None) -> "ExecutionResult":
        """Factory for FAILED result."""
        return cls(
            execution_id=execution_id,
            state=ExecutionResultState.FAILED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def cancelled(cls, execution_id: str, message: str = "",
                  metadata: Dict[str, Any] = None) -> "ExecutionResult":
        """Factory for CANCELLED result."""
        return cls(
            execution_id=execution_id,
            state=ExecutionResultState.CANCELLED,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def timed_out(cls, execution_id: str, message: str = "",
                  metadata: Dict[str, Any] = None) -> "ExecutionResult":
        """Factory for TIMED_OUT result."""
        return cls(
            execution_id=execution_id,
            state=ExecutionResultState.TIMED_OUT,
            message=message,
            metadata=metadata or {},
        )

    def is_success(self) -> bool:
        """Return True if the result is COMPLETED."""
        return self.state == ExecutionResultState.COMPLETED

    def is_terminal(self) -> bool:
        """All result states are terminal (non-transitionable further)."""
        return True

    def __repr__(self) -> str:
        return (
            f"ExecutionResult("
            f"id='{self.execution_id}', "
            f"state={self.state.value}, "
            f"msg='{self.message}')"
        )
