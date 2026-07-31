"""Execution Request (Sprint 251).

Program C - Real Execution Runtime.
Immutable request DTO for an execution, incl. support fields (timeout,
retries, cancellation token, execution id, provider id).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExecutionRequest:
    """Request eksekusi (immutable)."""
    execution_id: str
    provider_id: str
    operation: str
    payload: Dict[str, Any] = field(default_factory=dict)
    mode: str = "preview"  # preview | execute | rollback
    timeout_seconds: int = 60
    max_retries: int = 2
    cancellation_token: Optional[str] = None
    approved: bool = False
    approver: str = ""
    deterministic: bool = True
    synchronous: bool = True

    def __post_init__(self) -> None:
        if not self.execution_id:
            raise ValueError("execution_id is required")
        if not self.provider_id:
            raise ValueError("provider_id is required")
        if self.mode not in ("preview", "execute", "rollback"):
            raise ValueError("mode must be preview|execute|rollback")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "payload": dict(self.payload),
            "mode": self.mode,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "cancellation_token": self.cancellation_token,
            "approved": self.approved,
            "approver": self.approver,
            "deterministic": self.deterministic,
            "synchronous": self.synchronous,
        }
