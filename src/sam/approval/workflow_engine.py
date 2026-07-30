"""
Approval Workflow Engine.

Manages workflow phase transitions with validation.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .workflow import ApprovalWorkflow, WorkflowPhase, WorkflowTransition, PHASE_TRANSITIONS


class WorkflowTransitionError(Exception):
    pass


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: Dict[str, ApprovalWorkflow] = {}

    @property
    def workflow_count(self) -> int:
        return len(self._workflows)

    def create(self, workflow_id: str, normalized_id: str, owner: str = "") -> ApprovalWorkflow:
        wf = ApprovalWorkflow(workflow_id=workflow_id, normalized_id=normalized_id, owner=owner)
        self._workflows[workflow_id] = wf
        return wf

    def get(self, workflow_id: str) -> Optional[ApprovalWorkflow]:
        return self._workflows.get(workflow_id)

    def can_transition(self, workflow: ApprovalWorkflow, target: WorkflowPhase) -> bool:
        allowed = PHASE_TRANSITIONS.get(workflow.phase, [])
        return target in allowed

    def transition(self, workflow_id: str, target: WorkflowPhase, reason: str = "") -> ApprovalWorkflow:
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise WorkflowTransitionError(f"Workflow {workflow_id} not found")
        if not self.can_transition(wf, target):
            raise WorkflowTransitionError(
                f"Cannot transition from {wf.phase.name} to {target.name}")

        transition = WorkflowTransition(
            from_phase=wf.phase,
            to_phase=target,
            reason=reason,
            timestamp=datetime.now().timestamp(),
        )
        new_wf = ApprovalWorkflow(
            workflow_id=wf.workflow_id,
            normalized_id=wf.normalized_id,
            phase=target,
            history=list(wf.history) + [transition],
            owner=wf.owner,
        )
        self._workflows[workflow_id] = new_wf
        return new_wf

    def get_all(self) -> Dict[str, ApprovalWorkflow]:
        return dict(self._workflows)
