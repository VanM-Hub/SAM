"""Test audit record state transitions.

AUDIT_SPEC §Audit Lifecycle:
- Recorded → Verified
- Recorded → Archived
- Verified → Archived
- Archived is terminal
"""

import pytest
from src.sam.runtime.audit_recorder.state.audit_state import (
    AuditRecordState,
    LEGAL_AUDIT_TRANSITIONS,
    is_legal_audit_transition,
    get_legal_transitions,
)


class TestAuditRecordState:
    """Verify audit record state machine per AUDIT_SPEC L87-L100."""

    def test_three_states_defined(self):
        """Exactly 3 states: RECORDED, VERIFIED, ARCHIVED."""
        states = list(AuditRecordState)
        assert len(states) == 3
        assert AuditRecordState.RECORDED in states
        assert AuditRecordState.VERIFIED in states
        assert AuditRecordState.ARCHIVED in states

    def test_archived_is_terminal(self):
        """Archived is terminal — cannot transition further."""
        assert AuditRecordState.ARCHIVED.is_terminal is True
        assert AuditRecordState.RECORDED.is_terminal is False
        assert AuditRecordState.VERIFIED.is_terminal is False

    def test_recorded_can_go_to_verified(self):
        """Recorded → Verified is legal."""
        assert is_legal_audit_transition(
            AuditRecordState.RECORDED,
            AuditRecordState.VERIFIED,
        )

    def test_recorded_can_go_to_archived(self):
        """Recorded → Archived is legal."""
        assert is_legal_audit_transition(
            AuditRecordState.RECORDED,
            AuditRecordState.ARCHIVED,
        )

    def test_verified_can_go_to_archived(self):
        """Verified → Archived is legal."""
        assert is_legal_audit_transition(
            AuditRecordState.VERIFIED,
            AuditRecordState.ARCHIVED,
        )

    def test_archived_cannot_go_to_any(self):
        """Archived → anything is illegal."""
        assert not is_legal_audit_transition(
            AuditRecordState.ARCHIVED,
            AuditRecordState.RECORDED,
        )
        assert not is_legal_audit_transition(
            AuditRecordState.ARCHIVED,
            AuditRecordState.VERIFIED,
        )

    def test_verified_cannot_go_to_recorded(self):
        """Verified → Recorded is illegal."""
        assert not is_legal_audit_transition(
            AuditRecordState.VERIFIED,
            AuditRecordState.RECORDED,
        )

    def test_recorded_cannot_go_to_itself(self):
        """Same-state transition is illegal."""
        assert not is_legal_audit_transition(
            AuditRecordState.RECORDED,
            AuditRecordState.RECORDED,
        )

    def test_archived_has_empty_legal_transitions(self):
        """Archived transitions set is empty."""
        assert LEGAL_AUDIT_TRANSITIONS[AuditRecordState.ARCHIVED] == set()

    def test_get_legal_transitions_recorded(self):
        """Recorded → [VERIFIED, ARCHIVED]."""
        legal = get_legal_transitions(AuditRecordState.RECORDED)
        assert AuditRecordState.VERIFIED in legal
        assert AuditRecordState.ARCHIVED in legal
        assert len(legal) == 2

    def test_get_legal_transitions_verified(self):
        """Verified → [ARCHIVED]."""
        legal = get_legal_transitions(AuditRecordState.VERIFIED)
        assert legal == [AuditRecordState.ARCHIVED]

    def test_get_legal_transitions_archived(self):
        """Archived → [] (terminal)."""
        legal = get_legal_transitions(AuditRecordState.ARCHIVED)
        assert legal == []

    def test_enum_values(self):
        """Enum values are as expected."""
        assert AuditRecordState.RECORDED.value == "RECORDED"
        assert AuditRecordState.VERIFIED.value == "VERIFIED"
        assert AuditRecordState.ARCHIVED.value == "ARCHIVED"
