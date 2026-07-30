"""
Activation Engine.

Evaluates activation readiness for Approval Sessions.
Deterministic. Does NOT execute approval.
"""

import uuid
from datetime import datetime
from typing import Optional
from .approval_activation import ApprovalActivation, ActivationState, ActivationDecision, ActivationStatistics, ActivationSnapshot
from .approval_lifecycle import ApprovalLifecycle
from .activation_rules import ActivationRules
from .activation_history import ActivationHistory


class ActivationEngine:
    def __init__(self) -> None:
        self._activations: list = []
        self._history = ActivationHistory()

    def evaluate(self, lifecycle: ApprovalLifecycle, lifecycle_id: str, session_id: str) -> ApprovalActivation:
        readiness = ActivationRules.evaluate_readiness(lifecycle)
        blockers = ActivationRules.detect_blockers(lifecycle)
        state = ActivationRules.determine_state(readiness, blockers)
        decision = ActivationRules.determine_decision(readiness, blockers)

        activation = ApprovalActivation(
            activation_id=str(uuid.uuid4()),
            lifecycle_id=lifecycle_id,
            session_id=session_id,
            timestamp=datetime.now().timestamp(),
            state=state,
            decision=decision,
            blockers=list(blockers),
            readiness_score=readiness,
            ready=state == ActivationState.READY and not blockers,
        )
        self._activations.append(activation)
        self._history.record(activation.activation_id, "evaluated", state.name, decision.name)
        return activation

    def latest(self) -> Optional[ApprovalActivation]:
        return self._activations[-1] if self._activations else None

    @property
    def count(self) -> int: return len(self._activations)
    @property
    def history(self) -> ActivationHistory: return self._history

    def get_statistics(self) -> ActivationStatistics:
        counts = {"pending":0,"evaluated":0,"ready":0,"blocked":0,"invalid":0,"waiting":0}
        dec_counts = {"approved":0,"rejected":0,"held":0,"escalated":0}
        for a in self._activations:
            n = a.state.name.lower()
            if n in counts: counts[n] += 1
            d = a.decision.name.lower()
            if d in dec_counts: dec_counts[d] += 1
        return ActivationStatistics(total=self.count, **counts, **dec_counts)

    def create_snapshot(self) -> ActivationSnapshot:
        return ActivationSnapshot(
            snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
            activations=list(self._activations[-20:]),
            statistics=self.get_statistics()
        )
