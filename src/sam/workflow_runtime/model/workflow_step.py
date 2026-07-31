"""Workflow Step — langkah workflow (Sprint 197)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowStep:
    """Langkah workflow (immutable)."""
    step_id: str
    workflow_id: str = ""
    name: str = ""
    order: int = 0
    kind: str = "compose"
    depends_on: List[str] = field(default_factory=list)
    preview_only: bool = True
