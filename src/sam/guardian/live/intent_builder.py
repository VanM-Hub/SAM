"""
Guardian Intent Builder.

Builds operational intents from assessments, situations, transitions.
Deterministic, rule-based. No domain knowledge.
DTO only — does not execute anything.
"""

import uuid
from datetime import datetime
from typing import Optional

from .intent import GuardianIntent, IntentType, IntentPriority, IntentStatus
from .assessment import GuardianAssessment, AssessmentLevel, RiskLevel, PriorityLevel
from .situation import GuardianSituation, SituationType, SituationSeverity


class IntentBuilder:
    """Build intents from assessments and situations."""

    def build_from_assessment(self, assessment: GuardianAssessment) -> GuardianIntent:
        """Build an intent from an operational assessment."""
        intent_type = self._assessment_to_type(assessment)
        priority = self._assessment_to_priority(assessment)
        confidence = assessment.confidence

        return GuardianIntent(
            intent_id=str(uuid.uuid4()),
            intent_type=intent_type,
            priority=priority,
            status=IntentStatus.PENDING,
            timestamp=datetime.now().timestamp(),
            source_assessment_id=assessment.assessment_id,
            source_situation_id=assessment.situation_id,
            description=self._build_description(intent_type, assessment),
            confidence=confidence,
            affected_runtimes=list(assessment.affected_runtimes),
            evidence_count=assessment.evidence_count,
            policy_name=self._policy_for_type(intent_type),
            details={
                "assessment_level": assessment.level.name,
                "assessment_risk": assessment.risk.name,
                "assessment_priority": assessment.priority.name,
            },
        )

    def build_from_situation(self, situation: GuardianSituation) -> GuardianIntent:
        """Build a lightweight intent from a situation."""
        intent_type = self._situation_to_type(situation)
        priority = self._situation_to_priority(situation)

        return GuardianIntent(
            intent_id=str(uuid.uuid4()),
            intent_type=intent_type,
            priority=priority,
            status=IntentStatus.PENDING,
            timestamp=datetime.now().timestamp(),
            source_situation_id=situation.situation_id,
            description=f"From situation: {situation.situation_type.name}",
            confidence=70.0,
            affected_runtimes=list(situation.affected_runtimes),
            evidence_count=len(situation.related_transition_ids),
            policy_name=self._policy_for_type(intent_type),
            details={"situation_type": situation.situation_type.name, "severity": situation.severity.name},
        )

    def _assessment_to_type(self, a: GuardianAssessment) -> IntentType:
        if a.level == AssessmentLevel.CRITICAL:
            return IntentType.ESCALATE
        if a.level == AssessmentLevel.CONCERN:
            return IntentType.INVESTIGATE
        if a.risk == RiskLevel.HIGH or a.risk == RiskLevel.CRITICAL:
            return IntentType.REVIEW
        if a.level == AssessmentLevel.WARNING:
            return IntentType.MONITOR
        if a.level == AssessmentLevel.INFO or a.level == AssessmentLevel.POSITIVE:
            return IntentType.OBSERVE
        return IntentType.WAIT

    def _assessment_to_priority(self, a: GuardianAssessment) -> IntentPriority:
        if a.priority == PriorityLevel.URGENT:
            return IntentPriority.URGENT
        if a.priority == PriorityLevel.HIGH:
            return IntentPriority.HIGH
        if a.priority == PriorityLevel.NORMAL or a.level in (AssessmentLevel.CONCERN, AssessmentLevel.WARNING):
            return IntentPriority.NORMAL
        return IntentPriority.LOW

    def _situation_to_type(self, s: GuardianSituation) -> IntentType:
        mapping = {
            SituationType.HEALTHY: IntentType.OBSERVE,
            SituationType.BUSY: IntentType.MONITOR,
            SituationType.APPROVAL_BOTTLENECK: IntentType.REVIEW,
            SituationType.EXECUTION_DELAY: IntentType.INVESTIGATE,
            SituationType.RUNTIME_INSTABILITY: IntentType.INVESTIGATE,
            SituationType.RECOVERY: IntentType.MONITOR,
            SituationType.CONFIGURATION_DRIFT: IntentType.REVIEW,
            SituationType.RESOURCE_PRESSURE: IntentType.ESCALATE,
            SituationType.UNKNOWN: IntentType.OBSERVE,
        }
        return mapping.get(s.situation_type, IntentType.OBSERVE)

    def _situation_to_priority(self, s: GuardianSituation) -> IntentPriority:
        severity_map = {
            SituationSeverity.CRITICAL: IntentPriority.URGENT,
            SituationSeverity.HIGH: IntentPriority.HIGH,
            SituationSeverity.MEDIUM: IntentPriority.NORMAL,
            SituationSeverity.LOW: IntentPriority.LOW,
            SituationSeverity.INFO: IntentPriority.LOW,
        }
        return severity_map.get(s.severity, IntentPriority.LOW)

    def _build_description(self, t: IntentType, a: GuardianAssessment) -> str:
        descs = {
            IntentType.OBSERVE: f"Observe: {a.description}",
            IntentType.MONITOR: f"Monitor: {a.description}",
            IntentType.ESCALATE: f"ESCALATE: {a.description}",
            IntentType.RECOMMEND: f"Recommend: {a.description}",
            IntentType.INVESTIGATE: f"Investigate: {a.description}",
            IntentType.REVIEW: f"Review: {a.description}",
            IntentType.WAIT: f"Wait: {a.description}",
            IntentType.NO_ACTION: f"No action: {a.description}",
            IntentType.BLOCKED: f"BLOCKED: {a.description}",
        }
        return descs.get(t, f"Intent: {a.description}")

    def _policy_for_type(self, t: IntentType) -> str:
        mapping = {
            IntentType.OBSERVE: "observation",
            IntentType.MONITOR: "monitoring",
            IntentType.ESCALATE: "escalation",
            IntentType.RECOMMEND: "recommendation",
            IntentType.INVESTIGATE: "investigation",
            IntentType.REVIEW: "review",
            IntentType.WAIT: "wait",
            IntentType.NO_ACTION: "no_action",
            IntentType.BLOCKED: "blocked",
        }
        return mapping.get(t, "unknown")
