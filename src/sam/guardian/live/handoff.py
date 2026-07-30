"""
Guardian Handoff Engine.

Converts GuardianIntent into DecisionInput DTO.
Does NOT call Decision Runtime. Builds DTO only.
"""

import uuid
from datetime import datetime
from typing import Optional

from .intent import GuardianIntent, IntentType, IntentPriority, IntentStatus
from .decision_input import DecisionInput, DecisionCandidate, DecisionReason, DecisionMetadata, EligibilityStatus
from .mapping import IntentMapper
from .eligibility import EligibilityEngine


class HandoffEngine:
    """Converts GuardianIntent to DecisionInput. DTO only."""

    def __init__(self) -> None:
        self._mapper = IntentMapper()
        self._eligibility = EligibilityEngine()

    def handoff(self, intent: GuardianIntent) -> DecisionInput:
        """Convert an intent to a DecisionInput."""
        metadata = DecisionMetadata(
            source_intent_id=intent.intent_id,
            source_assessment_id=intent.source_assessment_id,
            source_situation_id=intent.source_situation_id,
            handoff_timestamp=datetime.now().timestamp(),
        )

        candidates = self._mapper.map(intent)
        reason = self._build_reason(intent, candidates)
        eligibility = self._eligibility.check(intent)
        priority_score = intent.priority.value
        confidence = intent.confidence

        return DecisionInput(
            input_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            metadata=metadata,
            candidates=candidates,
            reason=reason,
            eligibility=EligibilityStatus.ELIGIBLE if eligibility.eligible else
                       (EligibilityStatus.BLOCKED if eligibility.blocked else EligibilityStatus.NOT_ELIGIBLE),
            confidence=confidence,
            priority_score=priority_score,
        )

    def _build_reason(self, intent: GuardianIntent, candidates: list) -> DecisionReason:
        primary = f"Intent: {intent.intent_type.name} ({intent.policy_name})"
        details = [f"Confidence: {intent.confidence}", f"Priority: {intent.priority.name}"]
        return DecisionReason(primary=primary, details=details)
