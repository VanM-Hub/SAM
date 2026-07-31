"""Workflow Manifest — manifest workflow (Sprint 202)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowManifest:
    """Manifest workflow (immutable)."""
    version: str = "20.0.0"
    runtime: str = "workflow_runtime"
    subsystems: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "subsystems",
            self.subsystems or [
                "foundation", "model", "builder", "runtime", "catalog",
                "monitoring", "certification", "conversation", "dashboard",
            ],
        )
