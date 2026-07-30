"""
Guardian Situation Severity Calculator.

Calculates severity of situations based on rules.
All deterministic, rule-based. No AI.
Synchronous only.
"""

from typing import List, Dict, Any

from .transition import RuntimeTransition, ImpactLevel
from .situation import SituationCandidate, SituationSeverity


class SituationSeverityCalculator:
    """
    Rule-based severity calculator.

    Severity factors:
        - Number of transitions
        - Impact levels of transitions
        - Critical transition count
        - Number of affected runtimes
        - Duration of the situation
    """

    def calculate(
        self,
        candidate: SituationCandidate,
        all_transitions: List[RuntimeTransition],
    ) -> SituationSeverity:
        """
        Calculate severity for a situation candidate.

        Args:
            candidate: The situation candidate.
            all_transitions: All transitions for lookup.

        Returns:
            SituationSeverity level.
        """
        trans_by_id = {t.transition_id: t for t in all_transitions}
        related = [
            trans_by_id[tid] for tid in candidate.transition_ids
            if tid in trans_by_id
        ]

        if not related:
            return SituationSeverity.INFO

        # Count factors
        total = len(related)
        critical_count = sum(
            1 for t in related if t.impact == ImpactLevel.CRITICAL
        )
        high_count = sum(
            1 for t in related if t.impact == ImpactLevel.HIGH
        )
        medium_count = sum(
            1 for t in related if t.impact == ImpactLevel.MEDIUM
        )
        runtime_count = len(set(t.runtime_id for t in related))

        # Rule: CRITICAL
        if critical_count >= 1:
            return SituationSeverity.CRITICAL

        # Rule: HIGH
        if high_count >= 2:
            return SituationSeverity.HIGH
        if high_count >= 1 and medium_count >= 2:
            return SituationSeverity.HIGH
        if high_count >= 1 and runtime_count >= 2:
            return SituationSeverity.HIGH

        # Rule: MEDIUM
        if high_count >= 1:
            return SituationSeverity.MEDIUM
        if medium_count >= 3:
            return SituationSeverity.MEDIUM
        if total >= 5:
            return SituationSeverity.MEDIUM
        if runtime_count >= 3:
            return SituationSeverity.MEDIUM

        # Rule: LOW
        if medium_count >= 1 or total >= 2:
            return SituationSeverity.LOW

        # Rule: INFO
        return SituationSeverity.INFO

    def get_severity_score(self, severity: SituationSeverity) -> int:
        """Get numerical score for severity."""
        return severity.value
