"""
Guardian Eligibility Engine.

Determines if an intent is eligible for handoff.
Rule-based. No AI. Preview only.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .intent import GuardianIntent, IntentType, IntentPriority


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool = False
    blocked: bool = False
    reasons: List[str] = field(default_factory=list)


class EligibilityEngine:
    """Rule-based eligibility engine."""

    MIN_EVIDENCE = 1
    MIN_CONFIDENCE = 20.0
    ALLOWED_TYPES = {
        IntentType.OBSERVE, IntentType.MONITOR, IntentType.ESCALATE,
        IntentType.RECOMMEND, IntentType.INVESTIGATE, IntentType.REVIEW,
        IntentType.NO_ACTION,
    }
    BLOCKED_TYPES = {IntentType.BLOCKED, IntentType.WAIT}

    def check(self, intent: GuardianIntent) -> EligibilityResult:
        reasons = []

        # Evidence minimum
        if intent.evidence_count < self.MIN_EVIDENCE:
            reasons.append(f"Evidence too low: {intent.evidence_count} < {self.MIN_EVIDENCE}")

        # Confidence minimum
        if intent.confidence < self.MIN_CONFIDENCE:
            reasons.append(f"Confidence too low: {intent.confidence} < {self.MIN_CONFIDENCE}")

        # Blocked types
        if intent.intent_type in self.BLOCKED_TYPES:
            return EligibilityResult(eligible=False, blocked=True, reasons=["Blocked intent type"])

        # Allowed check
        if intent.intent_type not in self.ALLOWED_TYPES:
            reasons.append(f"Intent type not eligible: {intent.intent_type.name}")

        is_eligible = len(reasons) == 0
        return EligibilityResult(eligible=is_eligible, blocked=False, reasons=reasons)
