"""Workflow Descriptor — deskripsi workflow (Sprint 196)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowDescriptor:
    """Deskripsi workflow (immutable)."""
    id: str
    name: str
    category: str = "workflow"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    integrated_runtimes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id is required")
