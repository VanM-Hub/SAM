"""
Finalization Summary Builder.

Generates pipeline/decision/evidence/readiness/risk/integrity summary.
"""

from typing import Optional
from .finalization import FinalDecisionSummary, FinalDecisionRecord, FinalDecisionState
from .approval_certification import ApprovalCertification, CertificationState
from .approval_activation import ApprovalActivation, ActivationState


class FinalizationSummary:
    @staticmethod
    def build(certification: Optional[ApprovalCertification] = None,
              activation: Optional[ApprovalActivation] = None) -> FinalDecisionSummary:
        if not certification and not activation:
            return FinalDecisionSummary()

        cs = certification.state.name if certification else "UNKNOWN"
        ev = certification.evidence_count if certification else 0
        bl = certification.blocker_count if certification else 0
        rs = certification.readiness_score if certification else 0.0
        reqs = len(certification.requirements) if certification else 0
        passed = sum(1 for r in certification.requirements if r.met) if certification else 0
        as_ = activation.state.name if activation else "UNKNOWN"
        ls = activation.lifecycle_id if activation else ""

        return FinalDecisionSummary(
            pipeline_stages=17, total_checks=reqs, checks_passed=passed,
            readiness_score=rs, certification_state=cs,
            evidence_count=ev, blocker_count=bl,
            activation_state=as_, lifecycle_state=ls[:20],
        )

    @staticmethod
    def compute_integrity(certification: Optional[ApprovalCertification] = None,
                          activation: Optional[ApprovalActivation] = None) -> float:
        score = 0.0
        if certification: score += 0.3
        if activation: score += 0.2
        if certification and certification.certified: score += 0.3
        if certification and certification.evidence_count >= 5: score += 0.1
        if activation and activation.ready: score += 0.1
        return min(1.0, score)

    @staticmethod
    def compute_complete(certification: Optional[ApprovalCertification] = None,
                         activation: Optional[ApprovalActivation] = None) -> bool:
        return (certification is not None and activation is not None and
                certification.certification_id != "" and activation.activation_id != "")
