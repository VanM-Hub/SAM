"""
Alternative Generator for Sprint 54.

Generates decision alternatives based on evaluation.
Rule-based. Options only — not actions.
"""

from typing import List
import uuid
from .planning import DecisionAlternative
from .evaluation import DecisionEvaluation, ReadinessLevel


class AlternativeGeneratorS54:
    """Generates decision alternatives from evaluation."""

    def generate(self, evaluation: DecisionEvaluation) -> List[DecisionAlternative]:
        """Generate alternatives based on evaluation."""
        alternatives = []

        readiness = evaluation.ready
        confidence = evaluation.confidence

        # Alternative 1: Proceed (if ready or partial with high confidence)
        if readiness in (ReadinessLevel.READY, ReadinessLevel.PARTIAL):
            alt = DecisionAlternative(
                alternative_id=str(uuid.uuid4()),
                description="Proceed with decision",
                readiness=readiness,
                priority=self._priority_score(readiness, confidence),
                confidence=95.0 if readiness == ReadinessLevel.READY else 70.0,
                action_type="proceed",
                risks=[] if readiness == ReadinessLevel.READY else ["Partial readiness"],
                score=self._calculate_score(readiness, confidence),
            )
            alternatives.append(alt)

        # Alternative 2: Wait (always available)
        alternatives.append(DecisionAlternative(
            alternative_id=str(uuid.uuid4()),
            description="Wait for better conditions",
            readiness=ReadinessLevel.READY,
            priority=1,
            confidence=90.0,
            action_type="wait",
            risks=["Delay in decision execution"],
            score=60.0,
        ))

        # Alternative 3: Escalate (if blocked or high risk)
        if readiness == ReadinessLevel.BLOCKED or confidence in ("LOW", "MEDIUM"):
            alternatives.append(DecisionAlternative(
                alternative_id=str(uuid.uuid4()),
                description="Escalate for human review",
                readiness=ReadinessLevel.READY,
                priority=3,
                confidence=85.0,
                action_type="escalate",
                risks=["Human intervention delay"],
                score=75.0,
            ))

        # Sort by score descending
        alternatives.sort(key=lambda a: -a.score)
        return alternatives

    def _priority_score(self, readiness: str, confidence: str) -> int:
        if readiness == ReadinessLevel.READY:
            return 3
        if confidence in ("VERY_HIGH", "HIGH"):
            return 2
        return 1

    def _calculate_score(self, readiness: str, confidence: str) -> float:
        score = 0.0
        if readiness == ReadinessLevel.READY:
            score += 50
        elif readiness == ReadinessLevel.PARTIAL:
            score += 25
        if confidence == "VERY_HIGH":
            score += 40
        elif confidence == "HIGH":
            score += 30
        elif confidence == "MEDIUM":
            score += 15
        return score
