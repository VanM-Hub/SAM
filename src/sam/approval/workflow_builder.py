"""
Approval Workflow Builder.

Constructs ApprovalWorkflow from normalized intake records.
"""

from typing import Optional
from .workflow import ApprovalWorkflow
from .workflow_engine import WorkflowEngine
from .intake_normalizer import NormalizedApprovalRecord


class WorkflowBuilder:
    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine

    def build(self, normalized: NormalizedApprovalRecord, owner: str = "") -> ApprovalWorkflow:
        wf = self._engine.create(
            workflow_id=f"wf_{normalized.normalized_id}",
            normalized_id=normalized.normalized_id,
            owner=owner or normalized.label,
        )
        return wf
