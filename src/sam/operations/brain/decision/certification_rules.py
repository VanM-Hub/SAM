"""
Certification Rules.

Deterministic rule-based certification evaluation.
Does NOT execute approval. Preview only.
"""

from typing import List, Tuple
from .approval_certification import ApprovalCertification, CertificationRequirement
from .approval_activation import ApprovalActivation


class CertificationRules:
    REQUIREMENTS = [
        ("has_activation_id", True, "Activation ID must exist"),
        ("has_lifecycle_id", True, "Lifecycle ID must exist"),
        ("has_session_id", True, "Session ID must exist"),
        ("activation_evaluated", True, "Activation must be evaluated"),
        ("no_blockers", False, "No blockers detected"),
        ("readiness_above_0_6", True, "Readiness score >= 0.6"),
        ("lifecycle_valid", True, "Lifecycle must be at VALIDATED/READY/WAITING"),
    ]

    @staticmethod
    def evaluate_requirements(activation: ApprovalActivation) -> Tuple[List[CertificationRequirement], bool]:
        requirements = []
        all_met = True

        for key, required, desc in CertificationRules.REQUIREMENTS:
            met = False
            evidence = ""
            if key == "has_activation_id":
                met = bool(activation.activation_id)
                evidence = f"activation_id={activation.activation_id}" if met else "missing"
            elif key == "has_lifecycle_id":
                met = bool(activation.lifecycle_id)
                evidence = f"lifecycle_id={activation.lifecycle_id}" if met else "missing"
            elif key == "has_session_id":
                met = bool(activation.session_id)
                evidence = f"session_id={activation.session_id}" if met else "missing"
            elif key == "activation_evaluated":
                met = activation.state.name in ("READY", "WAITING", "BLOCKED", "EVALUATED")
                evidence = f"state={activation.state.name}"
            elif key == "no_blockers":
                met = len(activation.blockers) == 0
                evidence = f"blockers={len(activation.blockers)}"
            elif key == "readiness_above_0_6":
                met = activation.readiness_score >= 0.6
                evidence = f"score={activation.readiness_score}"
            elif key == "lifecycle_valid":
                met = activation.state.name in ("READY", "WAITING", "BLOCKED", "EVALUATED")
                evidence = f"activation_state={activation.state.name}"

            req = CertificationRequirement(name=key, met=met, required=required,
                                           description=desc, evidence=evidence)
            requirements.append(req)
            if required and not met:
                all_met = False

        return requirements, all_met

    @staticmethod
    def determine_state(readiness: float, blockers: int, all_met: bool) -> str:
        if all_met and readiness >= 0.9: return "CERTIFIED"
        if all_met and readiness >= 0.6: return "CONDITIONALLY_READY"
        if blockers > 0: return "BLOCKED"
        return "FAILED"

    @staticmethod
    def determine_decision(state: str) -> str:
        if state == "CERTIFIED": return "APPROVE"
        if state == "CONDITIONALLY_READY": return "CONDITIONAL"
        if state == "BLOCKED": return "REJECT"
        return "PENDING"

    @staticmethod
    def compute_evidence_count(reqs: List[CertificationRequirement]) -> int:
        return sum(1 for r in reqs if r.met)

    @staticmethod
    def compute_blocker_count(reqs: List[CertificationRequirement]) -> int:
        return sum(1 for r in reqs if r.required and not r.met)
