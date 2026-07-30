"""
Guardian Intent Ranker.

Ranks intents by priority based on multiple factors.
Deterministic, rule-based. No AI.
"""

from typing import List
from .intent import GuardianIntent, IntentPriority


class IntentRanker:
    """Rule-based intent ranker."""

    def rank(self, intents: List[GuardianIntent]) -> List[GuardianIntent]:
        """Rank intents by priority (urgent first), then confidence."""
        return sorted(
            intents,
            key=lambda i: (-i.priority.value, -i.confidence if i.confidence else 0),
        )

    def get_top(self, intents: List[GuardianIntent], n: int = 5) -> List[GuardianIntent]:
        """Get top N ranked intents."""
        ranked = self.rank(intents)
        return ranked[:n]

    def calculate_priority(
        self,
        assessment_priority: IntentPriority,
        confidence: float,
        evidence_count: int,
    ) -> IntentPriority:
        """Calculate priority based on multiple factors."""
        # URGENT if assessment already urgent
        if assessment_priority == IntentPriority.URGENT:
            return IntentPriority.URGENT

        # HIGH if assessment high + sufficient confidence
        if assessment_priority == IntentPriority.HIGH and confidence >= 60:
            return IntentPriority.HIGH

        # HIGH if assessment normal + high confidence + many evidence
        if assessment_priority == IntentPriority.NORMAL and confidence >= 80 and evidence_count >= 3:
            return IntentPriority.HIGH

        # NORMAL if assessment normal
        if assessment_priority == IntentPriority.NORMAL:
            return IntentPriority.NORMAL

        # LOW otherwise
        return IntentPriority.LOW
