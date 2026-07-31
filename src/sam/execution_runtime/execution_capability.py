"""Execution Capability (Sprint 250).

Program C - Real Execution Runtime.
Immutable capability model for an execution unit / provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import FrozenSet, Set


@dataclass(frozen=True)
class ExecutionCapability:
    """Kapabilitas eksekusi (immutable)."""
    capability_id: str
    owner_id: str
    supports_execute: bool = True
    supports_rollback: bool = True
    supports_cancellation: bool = True
    supports_timeout: bool = True
    operations: FrozenSet[str] = field(default_factory=frozenset)

    def can(self, operation: str) -> bool:
        return not self.operations or operation in self.operations

    def as_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "owner_id": self.owner_id,
            "supports_execute": self.supports_execute,
            "supports_rollback": self.supports_rollback,
            "supports_cancellation": self.supports_cancellation,
            "supports_timeout": self.supports_timeout,
            "operations": sorted(self.operations),
        }
