"""Audit Record State — AUDIT_SPEC §Audit Lifecycle.

Lifecycle states:
- Recorded: initial state after recording
- Verified: after successful verification (ADR-007)
- Archived: terminal state

Legal transitions per AUDIT_SPEC:
- Recorded -> Verified
- Recorded -> Archived
- Verified -> Archived
- Archived is terminal (no further transitions)
"""

from enum import Enum
from typing import Dict, List, Set


class AuditRecordState(str, Enum):
    """Audit record lifecycle states per AUDIT_SPEC L87-L100."""
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    ARCHIVED = "ARCHIVED"

    @property
    def is_terminal(self) -> bool:
        """Return True if this state is terminal (Archived)."""
        return self == AuditRecordState.ARCHIVED


# Legal transitions per AUDIT_SPEC L93-L98
LEGAL_AUDIT_TRANSITIONS: Dict[AuditRecordState, Set[AuditRecordState]] = {
    AuditRecordState.RECORDED: {
        AuditRecordState.VERIFIED,
        AuditRecordState.ARCHIVED,
    },
    AuditRecordState.VERIFIED: {
        AuditRecordState.ARCHIVED,
    },
    AuditRecordState.ARCHIVED: set(),  # Terminal
}


def is_legal_audit_transition(
    current: AuditRecordState,
    target: AuditRecordState,
) -> bool:
    """Return True if the transition is legal per AUDIT_SPEC L93-L98."""
    legal_targets = LEGAL_AUDIT_TRANSITIONS.get(current, set())
    return target in legal_targets


def get_legal_transitions(
    current: AuditRecordState,
) -> List[AuditRecordState]:
    """Return list of legal next states from current."""
    legal_targets = LEGAL_AUDIT_TRANSITIONS.get(current, set())
    return sorted(legal_targets, key=lambda s: s.value)
