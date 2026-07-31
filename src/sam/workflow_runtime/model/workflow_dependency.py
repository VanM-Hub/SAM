"""Workflow Dependency — dependensi workflow (Sprint 197)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowDependency:
    """Dependensi antar langkah (immutable)."""
    dependency_id: str
    workflow_id: str = ""
    from_step: str = ""
    to_step: str = ""
    constraints: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return bool(self.from_step and self.to_step)
