"""Execution Context (Sprint 251).

Program C - Real Execution Runtime.
Immutable context of an execution (task-level state).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ExecutionContext:
    """Konteks eksekusi (immutable)."""
    context_id: str
    execution_id: str
    provider_ids: tuple = field(default_factory=tuple)
    mode: str = "preview"
    input_payload: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "context_id": self.context_id,
            "execution_id": self.execution_id,
            "provider_ids": list(self.provider_ids),
            "mode": self.mode,
            "input_payload": dict(self.input_payload),
        }
