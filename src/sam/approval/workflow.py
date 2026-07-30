"""
Approval Workflow DTOs.

Defines workflow states and transitions for approval lifecycle.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum, auto


class WorkflowPhase(Enum):
    PENDING = auto()
    IN_REVIEW = auto()
    AWAITING_APPROVAL = auto()
    APPROVED = auto()
    REJECTED = auto()
    CANCELLED = auto()
    COMPLETED = auto()


PHASE_TRANSITIONS: Dict[WorkflowPhase, List[WorkflowPhase]] = {
    WorkflowPhase.PENDING: [WorkflowPhase.IN_REVIEW, WorkflowPhase.CANCELLED],
    WorkflowPhase.IN_REVIEW: [WorkflowPhase.AWAITING_APPROVAL, WorkflowPhase.REJECTED, WorkflowPhase.CANCELLED],
    WorkflowPhase.AWAITING_APPROVAL: [WorkflowPhase.APPROVED, WorkflowPhase.REJECTED, WorkflowPhase.CANCELLED],
    WorkflowPhase.APPROVED: [WorkflowPhase.COMPLETED, WorkflowPhase.REJECTED],
    WorkflowPhase.REJECTED: [],
    WorkflowPhase.CANCELLED: [],
    WorkflowPhase.COMPLETED: [],
}


@dataclass(frozen=True)
class WorkflowTransition:
    from_phase: WorkflowPhase = WorkflowPhase.PENDING
    to_phase: WorkflowPhase = WorkflowPhase.PENDING
    reason: str = ""
    timestamp: float = 0.0
    def to_dict(self) -> Dict[str, Any]: return {"from":self.from_phase.name,"to":self.to_phase.name,
        "reason":self.reason,"timestamp":self.timestamp}


@dataclass(frozen=True)
class ApprovalWorkflow:
    workflow_id: str = ""
    normalized_id: str = ""
    phase: WorkflowPhase = WorkflowPhase.PENDING
    history: List[WorkflowTransition] = field(default_factory=list)
    owner: str = ""
    def to_dict(self) -> Dict[str, Any]: return {"workflow_id":self.workflow_id,
        "normalized_id":self.normalized_id,"phase":self.phase.name,"owner":self.owner,
        "history":[h.to_dict() for h in self.history]}
