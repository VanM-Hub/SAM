"""
Guardian Risk Assessment.

Rule-based risk assessment across 7 dimensions.
Deterministic. No AI.
"""

from typing import Dict, Any, Optional
from .assessment import RiskLevel
from .situation import GuardianSituation, SituationType, SituationSeverity
from .transition import RuntimeTransition, ImpactLevel, TransitionType


class RiskAssessor:
    """
    Rule-based risk assessor.

    Dimensions:
        - Operational Risk
        - Execution Risk
        - Approval Risk
        - Runtime Risk
        - Consistency Risk
        - Recovery Risk
        - Overall Risk
    """

    def assess_situation(self, situation: GuardianSituation) -> RiskLevel:
        """Assess overall risk from a situation."""
        severity_map = {
            SituationSeverity.CRITICAL: RiskLevel.CRITICAL,
            SituationSeverity.HIGH: RiskLevel.HIGH,
            SituationSeverity.MEDIUM: RiskLevel.MEDIUM,
            SituationSeverity.LOW: RiskLevel.LOW,
            SituationSeverity.INFO: RiskLevel.NONE,
        }
        return severity_map.get(situation.severity, RiskLevel.LOW)

    def assess_transition(self, transition: RuntimeTransition) -> RiskLevel:
        impact_map = {
            ImpactLevel.CRITICAL: RiskLevel.CRITICAL,
            ImpactLevel.HIGH: RiskLevel.HIGH,
            ImpactLevel.MEDIUM: RiskLevel.MEDIUM,
            ImpactLevel.LOW: RiskLevel.LOW,
        }
        return impact_map.get(transition.impact, RiskLevel.LOW)

    def assess_operational(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type in (
            SituationType.RESOURCE_PRESSURE,
            SituationType.RUNTIME_INSTABILITY,
        ):
            return RiskLevel.HIGH
        if situation.situation_type == SituationType.BUSY:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def assess_execution(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type == SituationType.EXECUTION_DELAY:
            return RiskLevel.HIGH
        if situation.severity in (SituationSeverity.CRITICAL, SituationSeverity.HIGH):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def assess_approval(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type == SituationType.APPROVAL_BOTTLENECK:
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def assess_runtime(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type == SituationType.RUNTIME_INSTABILITY:
            return RiskLevel.HIGH
        if len(situation.affected_runtimes) > 2:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def assess_consistency(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type == SituationType.CONFIGURATION_DRIFT:
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def assess_recovery(self, situation: GuardianSituation) -> RiskLevel:
        if situation.situation_type == SituationType.RECOVERY:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def assess_all(self, situation: GuardianSituation) -> Dict[str, Any]:
        """Assess all risk dimensions for a situation."""
        op = self.assess_operational(situation)
        ex = self.assess_execution(situation)
        ap = self.assess_approval(situation)
        rt = self.assess_runtime(situation)
        co = self.assess_consistency(situation)
        rc = self.assess_recovery(situation)
        ov = self.assess_situation(situation)

        return {
            "operational": op.name,
            "execution": ex.name,
            "approval": ap.name,
            "runtime": rt.name,
            "consistency": co.name,
            "recovery": rc.name,
            "overall": ov.name,
        }
