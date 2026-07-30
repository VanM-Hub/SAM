"""
Certification Engine.

Determines readiness certification for Approval Runtime pipeline.
Does NOT execute approval. Preview only.
"""

import uuid
from datetime import datetime
from typing import Optional
from .approval_certification import ApprovalCertification, CertificationState, CertificationDecision, CertificationStatistics, CertificationSnapshot
from .approval_activation import ApprovalActivation
from .certification_rules import CertificationRules
from .certification_history import CertificationHistory


class CertificationEngine:
    def __init__(self) -> None:
        self._certifications: list = []
        self._history = CertificationHistory()

    def certify(self, activation: ApprovalActivation, activation_id: str, lifecycle_id: str) -> ApprovalCertification:
        reqs, all_met = CertificationRules.evaluate_requirements(activation)
        readiness = activation.readiness_score
        blockers = len(activation.blockers)
        state_name = CertificationRules.determine_state(readiness, blockers, all_met)
        decision_name = CertificationRules.determine_decision(state_name)
        ev_count = CertificationRules.compute_evidence_count(reqs)
        bk_count = CertificationRules.compute_blocker_count(reqs)
        state = CertificationState[state_name]
        decision = CertificationDecision[decision_name]

        cert = ApprovalCertification(
            certification_id=str(uuid.uuid4()),
            activation_id=activation_id,
            lifecycle_id=lifecycle_id,
            timestamp=datetime.now().timestamp(),
            state=state,
            decision=decision,
            requirements=reqs,
            readiness_score=readiness,
            certified=state == CertificationState.CERTIFIED,
            evidence_count=ev_count,
            blocker_count=bk_count,
        )
        self._certifications.append(cert)
        self._history.record(cert.certification_id, "certified", state_name, decision_name)
        return cert

    def latest(self) -> Optional[ApprovalCertification]:
        return self._certifications[-1] if self._certifications else None

    @property
    def count(self) -> int: return len(self._certifications)
    @property
    def history(self) -> CertificationHistory: return self._history

    def get_statistics(self) -> CertificationStatistics:
        counts = {"unknown":0,"certified":0,"conditionally_ready":0,"blocked":0,"failed":0}
        dec_counts = {"approved":0,"conditional":0,"rejected":0,"pending":0}
        for c in self._certifications:
            n = c.state.name.lower()
            if n in counts: counts[n] += 1
            d = c.decision.name.lower()
            if d in dec_counts: dec_counts[d] += 1
        return CertificationStatistics(total=self.count, **counts, **dec_counts)

    def create_snapshot(self) -> CertificationSnapshot:
        return CertificationSnapshot(
            snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
            certifications=list(self._certifications[-20:]),
            statistics=self.get_statistics()
        )
