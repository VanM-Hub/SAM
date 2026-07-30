"""
Guardian Priority Assessment.

Calculates priority based on severity, impact, duration, affected runtimes, and confidence.
All deterministic, rule-based. No AI.
"""

from typing import Dict, Any
from .assessment import PriorityLevel
from .situation import GuardianSituation, SituationSeverity
from .transition import RuntimeTransition, ImpactLevel


class PriorityAssessor:
    """
    Rule-based priority assessor.

    Factors:
        - Severity of the situation
        - Impact of transitions
        - Duration of the situation
        - Number of affected runtimes
    """

    def assess_situation(self, situation: GuardianSituation) -> PriorityLevel:
        """Assess priority from a situation."""
        # CRITICAL severity → URGENT
        if situation.severity == SituationSeverity.CRITICAL:
            return PriorityLevel.URGENT

        # HIGH severity + many runtimes → URGENT
        if situation.severity == SituationSeverity.HIGH:
            if len(situation.affected_runtimes) >= 2:
                return PriorityLevel.URGENT
            return PriorityLevel.HIGH

        # MEDIUM severity → HIGH if wide impact
        if situation.severity == SituationSeverity.MEDIUM:
            if len(situation.affected_runtimes) >= 3:
                return PriorityLevel.HIGH
            if situation.duration_seconds > 300:
                return PriorityLevel.HIGH
            return PriorityLevel.NORMAL

        # LOW severity → NORMAL
        if situation.severity == SituationSeverity.LOW:
            if len(situation.related_transition_ids) >= 5:
                return PriorityLevel.NORMAL
            return PriorityLevel.LOW

        # INFO → LOW
        return PriorityLevel.LOW

    def assess_transition(self, transition: RuntimeTransition) -> PriorityLevel:
        impact_map = {
            ImpactLevel.CRITICAL: PriorityLevel.URGENT,
            ImpactLevel.HIGH: PriorityLevel.HIGH,
            ImpactLevel.MEDIUM: PriorityLevel.NORMAL,
            ImpactLevel.LOW: PriorityLevel.LOW,
        }
        return impact_map.get(transition.impact, PriorityLevel.LOW)

    def get_priority_score(self, priority: PriorityLevel) -> int:
        return priority.value
