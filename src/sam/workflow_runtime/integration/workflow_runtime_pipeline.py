"""Workflow Runtime Pipeline — pipeline integrasi (Sprint 203).

Pipeline final:
Mission → Agent → Skill → Workflow → Memory → Knowledge → Cognitive
→ Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only — TIDAK mengubah runtime lain. Preview-only, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.workflow_registry import WorkflowRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "workflow", "memory", "knowledge",
    "cognitive", "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class WorkflowIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class WorkflowRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    workflow_id: str = ""
    stages: List[WorkflowIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class WorkflowRuntimePipeline:
    """Pipeline integrasi workflow. Read-only, deterministik, preview-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def run(self, workflow_id: str) -> WorkflowRuntimePipelineRun:
        stages = []
        for name in ["mission", "agent", "skill"]:
            stages.append(WorkflowIntegrationStage(name, True, "read-only"))
        exists = self._registry.exists(workflow_id)
        stages.append(WorkflowIntegrationStage(
            "workflow", exists, "found" if exists else "not found",
        ))
        if not exists:
            return WorkflowRuntimePipelineRun(
                ok=False, workflow_id=workflow_id, stages=stages, external_calls=0,
            )
        for name in ["memory", "knowledge", "cognitive", "orchestrator",
                     "connector", "provider"]:
            stages.append(WorkflowIntegrationStage(name, True, "read-only"))
        stages.append(WorkflowIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return WorkflowRuntimePipelineRun(
            ok=True, workflow_id=workflow_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
