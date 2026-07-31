"""Workflow Pipeline — pipeline workflow (Sprint 199)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowPipelineStage:
    """Satu tahap pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class WorkflowPipelineRun:
    """Hasil pipeline (immutable)."""
    ok: bool = False
    stages: List[WorkflowPipelineStage] = field(default_factory=list)
    external_calls: int = 0


class WorkflowPipeline:
    """Pipeline: Descriptor → Workflow → Builder → Preview."""

    STAGES = ["descriptor", "workflow", "builder", "preview"]

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def stages(self) -> List[str]:
        return list(self.STAGES)

    def run(self, workflow_id: str) -> WorkflowPipelineRun:
        ok = self._registry.exists(workflow_id)
        stages = [WorkflowPipelineStage(
            "descriptor", ok, "found" if ok else "not found",
        )]
        if not ok:
            return WorkflowPipelineRun(ok=False, stages=stages, external_calls=0)
        for name in ["workflow", "builder", "preview"]:
            stages.append(WorkflowPipelineStage(name, True, "read-only"))
        return WorkflowPipelineRun(ok=True, stages=stages, external_calls=0)
