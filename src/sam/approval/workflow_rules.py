"""
Approval Workflow Rules.

Governs allowed transitions and business rules for workflow phases.
"""

from typing import List, Dict, Any
from .workflow import WorkflowPhase, PHASE_TRANSITIONS


class WorkflowRules:
    @staticmethod
    def is_terminal(phase: WorkflowPhase) -> bool:
        return phase in (WorkflowPhase.REJECTED, WorkflowPhase.CANCELLED, WorkflowPhase.COMPLETED)

    @staticmethod
    def is_active(phase: WorkflowPhase) -> bool:
        return phase not in (WorkflowPhase.REJECTED, WorkflowPhase.CANCELLED, WorkflowPhase.COMPLETED)

    @staticmethod
    def get_allowed_transitions(phase: WorkflowPhase) -> List[WorkflowPhase]:
        return list(PHASE_TRANSITIONS.get(phase, []))

    @staticmethod
    def summary() -> Dict[str, Any]:
        return {p.name: [t.name for t in PHASE_TRANSITIONS.get(p, [])] for p in WorkflowPhase}
