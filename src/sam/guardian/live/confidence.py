"""
Guardian Confidence Engine.

Calculates confidence level based on evidence quality.
All deterministic. No probability, no AI.
Synchronous only.
"""

from typing import Dict, List, Any, Optional

from .assessment import AssessmentLevel
from .situation import GuardianSituation, SituationSeverity
from .transition import RuntimeTransition, ImpactLevel, TransitionType


class ConfidenceEngine:
    """
    Rule-based confidence calculator.

    Confidence factors (0-100):
        - Number of evidence items (transitions)
        - Consistency of evidence
        - History of similar situations
        - Rule agreement (how many rules triggered)
    """

    BASE_CONFIDENCE = 60.0

    def calculate(
        self,
        situation: Optional[GuardianSituation] = None,
        transitions: Optional[List[RuntimeTransition]] = None,
    ) -> float:
        """
        Calculate confidence for an assessment.

        Args:
            situation: The situation being assessed.
            transitions: Related transitions as evidence.

        Returns:
            Confidence score 0-100.
        """
        score = self.BASE_CONFIDENCE

        # Evidence count bonus
        if transitions:
            score += min(len(transitions) * 5.0, 25.0)
        if situation:
            score += min(len(situation.related_transition_ids) * 5.0, 25.0)

        # Consistency bonus
        if situation and transitions:
            if self._check_consistency(situation, transitions):
                score += 10.0

        # Cap at 100
        return min(score, 100.0)

    def calculate_from_transitions(
        self,
        transitions: List[RuntimeTransition],
    ) -> float:
        """
        Calculate confidence from transitions only.

        Args:
            transitions: List of transitions as evidence.

        Returns:
            Confidence score 0-100.
        """
        return self.calculate(transitions=transitions)

    def _check_consistency(
        self,
        situation: GuardianSituation,
        transitions: List[RuntimeTransition],
    ) -> bool:
        """
        Check if transitions are consistent with the situation type.

        Args:
            situation: The classified situation.
            transitions: The transitions that led to it.

        Returns:
            True if transitions match situation type.
        """
        if not transitions:
            return True

        has_critical = any(
            t.impact == ImpactLevel.CRITICAL for t in transitions
        )
        has_health = any(
            t.transition_type == TransitionType.HEALTH_CHANGED for t in transitions
        )
        has_version = any(
            t.transition_type == TransitionType.VERSION_CHANGED for t in transitions
        )

        # RESOURCE_PRESSURE should have critical transitions
        if situation.situation_type.name == "RESOURCE_PRESSURE" and not has_critical:
            return False

        # RUNTIME_INSTABILITY should have health transitions
        if situation.situation_type.name == "RUNTIME_INSTABILITY" and not has_health:
            return False

        # CONFIGURATION_DRIFT should have version transitions
        if situation.situation_type.name == "CONFIGURATION_DRIFT" and not has_version:
            return False

        return True

    def interpret(self, confidence: float) -> str:
        """Get a human-readable interpretation of confidence."""
        if confidence >= 90:
            return "HIGH_CONFIDENCE"
        elif confidence >= 75:
            return "GOOD_CONFIDENCE"
        elif confidence >= 50:
            return "MODERATE_CONFIDENCE"
        elif confidence >= 25:
            return "LOW_CONFIDENCE"
        else:
            return "POOR_CONFIDENCE"
