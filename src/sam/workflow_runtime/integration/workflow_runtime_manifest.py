"""Workflow Runtime Manifest — manifest integrasi (Sprint 203)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowRuntimeManifest:
    """Manifest runtime integrasi (immutable)."""
    version: str = "20.0.0"
    runtime: str = "workflow_runtime"
    integrated_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "integrated_runtimes",
            self.integrated_runtimes or [
                "mission", "agent", "skill", "memory", "knowledge",
                "cognitive", "orchestrator", "connector", "provider",
            ],
        )
