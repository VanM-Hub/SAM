"""Preview Builder — membangun preview DTO workflow (Sprint 198).

TIDAK scheduling, TIDAK reasoning, TIDAK memilih runtime, TIDAK inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..model.workflow import Workflow


@dataclass(frozen=True)
class WorkflowPreviewDTO:
    """Preview workflow (immutable)."""
    label: str = ""
    workflow: Workflow = None
    composed: bool = True
    scheduled: bool = False
    external_calls: int = 0

    def __post_init__(self) -> None:
        if self.workflow is None:
            object.__setattr__(self, "workflow", Workflow(""))
        if self.scheduled:
            raise ValueError("preview must not schedule")
        if self.external_calls != 0:
            raise ValueError("preview must have 0 external calls")


class PreviewBuilder:
    """Builder preview. Menyusun DTO — tidak pernah scheduling/infer."""

    def build(self, label: str, workflow: Workflow) -> WorkflowPreviewDTO:
        return WorkflowPreviewDTO(label=label, workflow=workflow)
