"""
Guardian Intent Mapping.

Maps intents to DecisionCandidates. Rule-based. No domain knowledge.
"""

from typing import List, Dict
import uuid

from .intent import GuardianIntent, IntentType
from .decision_input import DecisionCandidate


class IntentMapper:
    """Maps intents to decision candidates."""

    _ACTION_MAP: Dict[IntentType, str] = {
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

    def map(self, intent: GuardianIntent) -> List[DecisionCandidate]:
        """Map an intent to decision candidates."""
        candidates = []
        action = self._ACTION_MAP.get(intent.intent_type, "unknown")

        for rid in intent.affected_runtimes:
            candidate = DecisionCandidate(
                candidate_id=str(uuid.uuid4()),
                runtime_id=rid,
                action_type=action,
                priority=intent.priority.value,
                confidence=intent.confidence,
                evidence_count=intent.evidence_count,
                details={
                    "intent_type": intent.intent_type.name,
                    "policy": intent.policy_name,
                },
            )
            candidates.append(candidate)

        return candidates
