"""Execution Option (Sprint 251).

Program C - Real Execution Runtime.
Immutable representation of a selectable execution option (timeout/retries/
provider preference).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ExecutionOption:
    """Opsi eksekusi (immutable)."""
    option_id: str
    name: str
    provider_id: str = ""
    timeout_seconds: int = 60
    max_retries: int = 2
    cancellable: bool = True
    rollback: bool = True
    deterministic: bool = True

    def as_dict(self) -> dict:
        return {
            "option_id": self.option_id,
            "name": self.name,
            "provider_id": self.provider_id,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "cancellable": self.cancellable,
            "rollback": self.rollback,
            "deterministic": self.deterministic,
        }
