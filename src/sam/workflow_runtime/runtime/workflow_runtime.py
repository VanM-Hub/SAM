"""Workflow Runtime — engine utama runtime workflow (Sprint 199)."""
from __future__ import annotations
from dataclasses import dataclass, field

from ..model.workflow import Workflow
from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowRunResult:
    """Hasil run runtime workflow (immutable)."""
    ok: bool = True
    workflow_id: str = ""
    workflow: Workflow = field(default_factory=lambda: Workflow(""))
    external_calls: int = 0
    scheduled: bool = False


class WorkflowRuntime:
    """Runtime workflow. Deterministik, preview-only, tanpa scheduling/inferensi."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def run(self, workflow_id: str) -> WorkflowRunResult:
        if not self._registry.exists(workflow_id):
            return WorkflowRunResult(ok=False, workflow_id=workflow_id, external_calls=0)
        return WorkflowRunResult(
            ok=True, workflow_id=workflow_id,
            workflow=Workflow(workflow_id=workflow_id),
            external_calls=0, scheduled=False,
        )

    def engine_info(self) -> dict:
        return {
            "runtime": "workflow_runtime",
            "no_inference": True,
            "preview_only": True,
        }
