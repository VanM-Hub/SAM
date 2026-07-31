"""Execution Response (Sprint 251).

Program C - Real Execution Runtime.
Immutable result of an execution. In preview external_calls == 0; in
execute mode with valid approval external_calls may be > 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionResponse:
    """Response eksekusi (immutable)."""
    execution_id: str
    provider_id: str
    operation: str
    status: str = "pending"  # pending|executing|completed|failed|cancelled|timeout
    payload: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    mode: str = "preview"
    external_calls: int = 0
    retries_used: int = 0
    duration_ms: int = 0
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.status == "completed"

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "status": self.status,
            "payload": dict(self.payload),
            "message": self.message,
            "mode": self.mode,
            "external_calls": self.external_calls,
            "retries_used": self.retries_used,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }
