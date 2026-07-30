"""
Lifecycle Rules.

Deterministic rule-based transitions for ApprovalSession lifecycle.
"""

from typing import Dict, Optional
from .approval_lifecycle import ApprovalLifecycleState


# Valid transitions map: (from_state) -> list of (to_state, condition_check_required)
_VALID_TRANSITIONS = {
    ApprovalLifecycleState.CREATED: {
        "to": [ApprovalLifecycleState.VALIDATED, ApprovalLifecycleState.CANCELLED],
        "label": "created"
    },
    ApprovalLifecycleState.VALIDATED: {
        "to": [ApprovalLifecycleState.READY, ApprovalLifecycleState.CANCELLED],
        "label": "validated"
    },
    ApprovalLifecycleState.READY: {
        "to": [ApprovalLifecycleState.WAITING, ApprovalLifecycleState.CANCELLED],
        "label": "ready"
    },
    ApprovalLifecycleState.WAITING: {
        "to": [ApprovalLifecycleState.READY, ApprovalLifecycleState.CANCELLED, ApprovalLifecycleState.CLOSED],
        "label": "waiting"
    },
    ApprovalLifecycleState.CANCELLED: {
        "to": [ApprovalLifecycleState.CLOSED],
        "label": "cancelled"
    },
    ApprovalLifecycleState.CLOSED: {
        "to": [],
        "label": "closed"
    },
}


class LifecycleRules:
    @staticmethod
    def allowed_transitions(state: ApprovalLifecycleState) -> list:
        entry = _VALID_TRANSITIONS.get(state)
        if not entry: return []
        return list(entry["to"])

    @staticmethod
    def can_transition(current: ApprovalLifecycleState, target: ApprovalLifecycleState) -> bool:
        return target in LifecycleRules.allowed_transitions(current)

    @staticmethod
    def is_final(state: ApprovalLifecycleState) -> bool:
        return state == ApprovalLifecycleState.CLOSED

    @staticmethod
    def is_cancellable(state: ApprovalLifecycleState) -> bool:
        return not LifecycleRules.is_final(state) and state != ApprovalLifecycleState.CANCELLED

    @staticmethod
    def is_active(state: ApprovalLifecycleState) -> bool:
        return state in (ApprovalLifecycleState.CREATED, ApprovalLifecycleState.VALIDATED,
                         ApprovalLifecycleState.READY, ApprovalLifecycleState.WAITING)

    @staticmethod
    def next_expected(state: ApprovalLifecycleState) -> Optional[str]:
        allowed = LifecycleRules.allowed_transitions(state)
        if not allowed: return None
        return allowed[0].name if allowed else None
