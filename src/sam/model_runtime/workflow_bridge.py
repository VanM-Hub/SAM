"""Workflow Bridge — bridge model <-> workflow (read-only) (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke Workflow Runtime; tidak menjalankan workflow.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkflowBridgeView:
    """View read-only workflow (immutable)."""
    workflow_id: str = ""
    steps_hint: int = 0
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "steps_hint": self.steps_hint,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class WorkflowBridge:
    """Bridge model <-> workflow. Read-only, tidak mengeksekusi workflow."""

    def view(self, workflow_id: str, steps_hint: int = 0) -> WorkflowBridgeView:
        return WorkflowBridgeView(
            workflow_id=workflow_id,
            steps_hint=steps_hint,
            preview_only=True,
            external_calls=0,
        )
