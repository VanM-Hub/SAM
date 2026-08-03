"""Tests for SessionLifecycle."""

import pytest
from sam.compliance import SessionState, SessionLifecycle
from sam.compliance.exceptions.compliance_errors import InvalidSessionStateError, SessionImmutableError


class TestLifecycleTransitions:
    """Valid lifecycle transitions per P1-001 §7.1."""

    def test_initial_state(self):
        lc = SessionLifecycle()
        assert lc.state == SessionState.INITIATED

    def test_normal_flow(self):
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        assert lc.state == SessionState.EVIDENCE_COLLECTION
        lc.transition_to(SessionState.ANALYSIS)
        assert lc.state == SessionState.ANALYSIS
        lc.transition_to(SessionState.PRELIMINARY_VERDICT)
        assert lc.state == SessionState.PRELIMINARY_VERDICT
        lc.transition_to(SessionState.FINAL_VERDICT)
        assert lc.state == SessionState.FINAL_VERDICT
        lc.transition_to(SessionState.ARCHIVED)
        assert lc.state == SessionState.ARCHIVED

    def test_skip_review(self):
        """Can go directly from PRELIMINARY_VERDICT to FINAL_VERDICT (skip REVIEW)."""
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        lc.transition_to(SessionState.ANALYSIS)
        lc.transition_to(SessionState.PRELIMINARY_VERDICT)
        lc.transition_to(SessionState.FINAL_VERDICT)
        assert lc.state == SessionState.FINAL_VERDICT

    def test_with_review(self):
        """Can go PRELIMINARY_VERDICT → REVIEW → FINAL_VERDICT."""
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        lc.transition_to(SessionState.ANALYSIS)
        lc.transition_to(SessionState.PRELIMINARY_VERDICT)
        lc.transition_to(SessionState.REVIEW)
        assert lc.state == SessionState.REVIEW
        lc.transition_to(SessionState.FINAL_VERDICT)
        assert lc.state == SessionState.FINAL_VERDICT


class TestLifecycleInvalidTransitions:
    """Invalid transitions must raise errors."""

    def test_cannot_skip_states(self):
        lc = SessionLifecycle()
        with pytest.raises(InvalidSessionStateError):
            lc.transition_to(SessionState.ANALYSIS)  # skips EVIDENCE_COLLECTION

    def test_cannot_go_backwards(self):
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        with pytest.raises(InvalidSessionStateError):
            lc.transition_to(SessionState.INITIATED)

    def test_cannot_transition_from_terminal(self):
        lc = SessionLifecycle()
        for s in [SessionState.EVIDENCE_COLLECTION, SessionState.ANALYSIS,
                  SessionState.PRELIMINARY_VERDICT, SessionState.FINAL_VERDICT,
                  SessionState.ARCHIVED]:
            lc.transition_to(s)

        with pytest.raises(SessionImmutableError):
            lc.transition_to(SessionState.INITIATED)

    def test_review_cannot_go_to_analysis(self):
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        lc.transition_to(SessionState.ANALYSIS)
        lc.transition_to(SessionState.PRELIMINARY_VERDICT)
        lc.transition_to(SessionState.REVIEW)
        # REVIEW → ANALYSIS is backwards
        with pytest.raises(InvalidSessionStateError):
            lc.transition_to(SessionState.ANALYSIS)


class TestLifecycleCanTransition:
    """can_transition_to predicates."""

    def test_can_transition_valid(self):
        lc = SessionLifecycle()
        assert lc.can_transition_to(SessionState.EVIDENCE_COLLECTION)
        assert not lc.can_transition_to(SessionState.ANALYSIS)

    def test_can_transition_terminal(self):
        lc = SessionLifecycle()
        for s in [SessionState.EVIDENCE_COLLECTION, SessionState.ANALYSIS,
                  SessionState.PRELIMINARY_VERDICT, SessionState.FINAL_VERDICT,
                  SessionState.ARCHIVED]:
            lc.transition_to(s)
        assert not lc.can_transition_to(SessionState.INITIATED)


class TestLifecycleUtility:
    """Utility methods."""

    def test_is_terminal(self):
        lc = SessionLifecycle()
        assert not lc.is_terminal()
        # Navigate to FINAL_VERDICT — not terminal (can still transition to ARCHIVED)
        for s in [SessionState.EVIDENCE_COLLECTION, SessionState.ANALYSIS,
                  SessionState.PRELIMINARY_VERDICT, SessionState.FINAL_VERDICT]:
            lc.transition_to(s)
        assert not lc.is_terminal()  # FINAL_VERDICT can still go to ARCHIVED
        lc.transition_to(SessionState.ARCHIVED)
        assert lc.is_terminal()  # ARCHIVED is truly terminal

    def test_is_active(self):
        lc = SessionLifecycle()
        assert not lc.is_active()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        assert lc.is_active()

    def test_reset(self):
        lc = SessionLifecycle()
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)
        lc.transition_to(SessionState.ANALYSIS)
        lc.reset()
        assert lc.state == SessionState.INITIATED
        assert not lc.is_terminal()

    def test_valid_transitions(self):
        trans = SessionLifecycle.valid_transitions(SessionState.INITIATED)
        assert SessionState.EVIDENCE_COLLECTION in trans
        assert SessionState.ANALYSIS not in trans

    def test_valid_transitions_archived(self):
        trans = SessionLifecycle.valid_transitions(SessionState.ARCHIVED)
        assert len(trans) == 0


class TestLifecycleResetAfterTerminal:
    """Reset should work from any state."""

    def test_reset_from_final_verdict(self):
        lc = SessionLifecycle()
        for s in [SessionState.EVIDENCE_COLLECTION, SessionState.ANALYSIS,
                  SessionState.PRELIMINARY_VERDICT, SessionState.FINAL_VERDICT]:
            lc.transition_to(s)
        lc.reset()
        assert lc.state == SessionState.INITIATED
        lc.transition_to(SessionState.EVIDENCE_COLLECTION)

    def test_reset_from_archived(self):
        lc = SessionLifecycle()
        for s in [SessionState.EVIDENCE_COLLECTION, SessionState.ANALYSIS,
                  SessionState.PRELIMINARY_VERDICT, SessionState.FINAL_VERDICT,
                  SessionState.ARCHIVED]:
            lc.transition_to(s)
        lc.reset()
        assert lc.state == SessionState.INITIATED
