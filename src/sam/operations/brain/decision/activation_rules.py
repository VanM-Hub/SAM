"""
Activation Rules.

Deterministic rule-based activation evaluation.
Does NOT execute approval. Preview only.
"""

from typing import List
from .approval_activation import ActivationState, ActivationDecision
from .approval_lifecycle import ApprovalLifecycle


class ActivationRules:
    @staticmethod
    def evaluate_readiness(lifecycle: ApprovalLifecycle) -> float:
        """Score 0.0-1.0 based on lifecycle state & transitions."""
        score = 0.0
        if lifecycle.session_ready: score += 0.3
        if lifecycle.state.name == "READY": score += 0.3
        elif lifecycle.state.name == "WAITING": score += 0.2
        elif lifecycle.state.name == "VALIDATED": score += 0.1
        if len(lifecycle.transitions) >= 1: score += 0.2
        # bonus for proper chain
        expected = ["CREATED","VALIDATED","READY","WAITING","CLOSED"]
        seen = [t.to_state for t in lifecycle.transitions] + [lifecycle.state.name]
        match = sum(1 for s in expected[:len(seen)] if len(seen) > 0 and len(seen) <= len(expected) and seen[len(seen)-1] != "CANCELLED")
        if "CANCELLED" not in seen and "CLOSED" not in seen: score += 0.2
        return min(1.0, score)

    @staticmethod
    def detect_blockers(lifecycle: ApprovalLifecycle) -> List[str]:
        blockers = []
        if not lifecycle.session_id: blockers.append("Missing session ID")
        if not lifecycle.lifecycle_id: blockers.append("Missing lifecycle ID")
        if not lifecycle.session_ready: blockers.append("Session not ready")
        if lifecycle.state.name == "CANCELLED": blockers.append("Session was cancelled")
        if lifecycle.state.name == "CLOSED": blockers.append("Session already closed")
        return blockers

    @staticmethod
    def determine_state(readiness: float, blockers: List[str]) -> ActivationState:
        if blockers: return ActivationState.BLOCKED
        if readiness >= 0.8: return ActivationState.READY
        if readiness >= 0.5: return ActivationState.WAITING
        return ActivationState.PENDING

    @staticmethod
    def determine_decision(readiness: float, blockers: List[str]) -> ActivationDecision:
        if blockers: return ActivationDecision.HOLD
        if readiness >= 0.8: return ActivationDecision.APPROVE
        if readiness >= 0.5: return ActivationDecision.ESCALATE
        return ActivationDecision.NONE

    @staticmethod
    def is_activatable(activation) -> bool:
        return activation.state == ActivationState.READY and activation.ready
