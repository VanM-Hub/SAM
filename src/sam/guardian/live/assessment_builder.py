"""
Guardian Assessment Builder.

Builds assessments from situations, transitions, and synchronization data.
All deterministic, rule-based. No AI. No domain knowledge.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from collections import defaultdict

from .assessment import (
    GuardianAssessment, AssessmentLevel, AssessmentCategory,
    RiskLevel, PriorityLevel,
)
from .situation import GuardianSituation, SituationType, SituationSeverity
from .transition import RuntimeTransition, ImpactLevel, TransitionType
from .risk_assessment import RiskAssessor
from .priority_assessment import PriorityAssessor
from .confidence import ConfidenceEngine


class AssessmentBuilder:
    """
    Builds assessments from operational data.

    Converts situations → assessments using rule-based logic.
    Does NOT know domain, storage, or repository.
    """

    def __init__(self) -> None:
        self._risk_assessor = RiskAssessor()
        self._priority_assessor = PriorityAssessor()
        self._confidence_engine = ConfidenceEngine()

    def build_from_situation(
        self,
        situation: GuardianSituation,
        transitions: Optional[List[RuntimeTransition]] = None,
    ) -> GuardianAssessment:
        """
        Build an assessment from a situation.

        Args:
            situation: The situation to assess.
            transitions: Optional related transitions for evidence.

        Returns:
            GuardianAssessment for this situation.
        """
        category = self._determine_category(situation)
        level = self._determine_level(situation)
        risk = self._risk_assessor.assess_situation(situation)
        priority = self._priority_assessor.assess_situation(situation)
        confidence = self._confidence_engine.calculate(
            situation=situation,
            transitions=transitions,
        )

        return GuardianAssessment(
            assessment_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            situation_id=situation.situation_id,
            category=category,
            level=level,
            risk=risk,
            priority=priority,
            confidence=confidence,
            description=self._build_description(situation, level),
            affected_runtimes=list(situation.affected_runtimes),
            evidence_count=len(situation.related_transition_ids),
            details={
                "situation_type": situation.situation_type.name,
                "situation_severity": situation.severity.name,
                "transition_count": len(situation.related_transition_ids),
                "duration_seconds": situation.duration_seconds,
            },
        )

    def build_from_transition(
        self,
        transition: RuntimeTransition,
    ) -> GuardianAssessment:
        """Build a lightweight assessment from a single transition."""
        category = AssessmentCategory.OPERATIONAL_RISK
        level = self._transition_to_level(transition)
        risk = self._risk_assessor.assess_transition(transition)
        priority = self._priority_assessor.assess_transition(transition)

        return GuardianAssessment(
            assessment_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            situation_id="",
            category=category,
            level=level,
            risk=risk,
            priority=priority,
            confidence=85.0,
            description=f"Transition: {transition.transition_type.name} on {transition.runtime_id}",
            affected_runtimes=[transition.runtime_id],
            evidence_count=1,
            details={
                "transition_type": transition.transition_type.name,
                "impact": transition.impact.name,
            },
        )

    def _determine_category(self, situation: GuardianSituation) -> AssessmentCategory:
        mapping = {
            SituationType.HEALTHY: AssessmentCategory.OVERALL_HEALTH,
            SituationType.BUSY: AssessmentCategory.PERFORMANCE,
            SituationType.APPROVAL_BOTTLENECK: AssessmentCategory.APPROVAL_RISK,
            SituationType.EXECUTION_DELAY: AssessmentCategory.EXECUTION_RISK,
            SituationType.RUNTIME_INSTABILITY: AssessmentCategory.RUNTIME_RISK,
            SituationType.RECOVERY: AssessmentCategory.RECOVERY_RISK,
            SituationType.CONFIGURATION_DRIFT: AssessmentCategory.CONSISTENCY_RISK,
            SituationType.RESOURCE_PRESSURE: AssessmentCategory.OPERATIONAL_RISK,
            SituationType.UNKNOWN: AssessmentCategory.STABILITY,
        }
        return mapping.get(situation.situation_type, AssessmentCategory.STABILITY)

    def _determine_level(self, situation: GuardianSituation) -> AssessmentLevel:
        severity_map = {
            SituationSeverity.CRITICAL: AssessmentLevel.CRITICAL,
            SituationSeverity.HIGH: AssessmentLevel.CONCERN,
            SituationSeverity.MEDIUM: AssessmentLevel.WARNING,
            SituationSeverity.LOW: AssessmentLevel.INFO,
            SituationSeverity.INFO: AssessmentLevel.POSITIVE,
        }
        return severity_map.get(situation.severity, AssessmentLevel.INFO)

    def _transition_to_level(self, t: RuntimeTransition) -> AssessmentLevel:
        mapping = {
            ImpactLevel.CRITICAL: AssessmentLevel.CRITICAL,
            ImpactLevel.HIGH: AssessmentLevel.CONCERN,
            ImpactLevel.MEDIUM: AssessmentLevel.WARNING,
            ImpactLevel.LOW: AssessmentLevel.INFO,
        }
        return mapping.get(t.impact, AssessmentLevel.INFO)

    def _build_description(self, s: GuardianSituation, lvl: AssessmentLevel) -> str:
        if lvl == AssessmentLevel.CRITICAL:
            return f"CRITICAL: {s.situation_type.name} — immediate attention required"
        if lvl == AssessmentLevel.CONCERN:
            return f"CONCERN: {s.situation_type.name} — review recommended"
        if lvl == AssessmentLevel.WARNING:
            return f"WARNING: {s.situation_type.name} — monitor closely"
        if lvl == AssessmentLevel.INFO:
            return f"INFO: {s.situation_type.name} — no action needed"
        return f"{s.situation_type.name}: {s.description}"
