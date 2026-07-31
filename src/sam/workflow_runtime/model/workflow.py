"""Workflow — model workflow (Sprint 197)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Workflow:
    """Workflow (immutable)."""
    workflow_id: str
    name: str = ""
    steps: List[str] = field(default_factory=list)
    scope: str = "process"
    preview_only: bool = True

    def step_count(self) -> int:
        return len(self.steps)
