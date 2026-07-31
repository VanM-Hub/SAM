"""Workflow Capability — kapabilitas workflow (Sprint 196)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowCapability:
    """Kapabilitas workflow (immutable). Deterministik, tanpa inferensi."""
    id: str
    owner_id: str = ""
    operations: List[str] = field(default_factory=list)
    deterministic: bool = True
    no_inference: bool = True

    def supports(self, operation: str) -> bool:
        return operation in self.operations
