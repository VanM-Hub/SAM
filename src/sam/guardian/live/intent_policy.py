"""
Guardian Intent Policy Engine.

Built-in policies for operational intents.
Rule-based. No AI. No domain knowledge.
"""

from typing import Dict, Any, Optional
from .intent import GuardianIntent, IntentType, IntentPriority, ValidationResult


class IntentPolicyEngine:
    """Rule-based policy engine for intents."""

    def __init__(self) -> None:
        self._policies = {
            IntentType.OBSERVE: self._policy_observe,
            IntentType.MONITOR: self._policy_monitor,
            IntentType.ESCALATE: self._policy_escalate,
            IntentType.RECOMMEND: self._policy_recommend,
            IntentType.INVESTIGATE: self._policy_investigate,
            IntentType.REVIEW: self._policy_review,
            IntentType.WAIT: self._policy_wait,
            IntentType.NO_ACTION: self._policy_no_action,
            IntentType.BLOCKED: self._policy_blocked,
        }

    def apply_policy(self, intent: GuardianIntent) -> Dict[str, Any]:
        """Apply policy rules to an intent and return policy result."""
        policy_fn = self._policies.get(intent.intent_type, self._policy_observe)
        result = policy_fn(intent)
        return {
            "intent_id": intent.intent_id,
            "policy": intent.policy_name,
            "result": result,
        }

    def _policy_observe(self, intent: GuardianIntent) -> str:
        if intent.priority == IntentPriority.LOW:
            return "observe_only"
        return "observe_with_attention"

    def _policy_monitor(self, intent: GuardianIntent) -> str:
        if intent.priority >= IntentPriority.HIGH:
            return "monitor_close"
        return "monitor_periodic"

    def _policy_escalate(self, intent: GuardianIntent) -> str:
        if intent.confidence >= 80:
            return "escalate_immediate"
        if intent.confidence >= 50:
            return "escalate_with_caution"
        return "escalate_pending_evidence"

    def _policy_recommend(self, intent: GuardianIntent) -> str:
        if intent.priority == IntentPriority.URGENT:
            return "recommend_urgent"
        return "recommend_normal"

    def _policy_investigate(self, intent: GuardianIntent) -> str:
        if intent.evidence_count >= 3:
            return "investigate_detailed"
        return "investigate_preliminary"

    def _policy_review(self, intent: GuardianIntent) -> str:
        if intent.priority >= IntentPriority.HIGH:
            return "review_priority"
        return "review_routine"

    def _policy_wait(self, intent: GuardianIntent) -> str:
        return "wait_for_evidence"

    def _policy_no_action(self, intent: GuardianIntent) -> str:
        return "no_action_needed"

    def _policy_blocked(self, intent: GuardianIntent) -> str:
        return "blocked_requires_intervention"

    def validate(self, intent: GuardianIntent) -> ValidationResult:
        """Validate intent against policies."""
        errors = []
        warnings = []

        if intent.confidence < 20 and intent.priority.value >= IntentPriority.HIGH.value:
            warnings.append("High priority with low confidence")

        if intent.intent_type == IntentType.ESCALATE and intent.priority.value < IntentPriority.HIGH.value:
            warnings.append("Escalate intent with non-high priority")

        if intent.intent_type == IntentType.NO_ACTION and intent.priority.value >= IntentPriority.HIGH.value:
            errors.append("No action intent with high/urgent priority")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
