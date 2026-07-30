"""
Guardian Intent Validator.

Validates intents for consistency and correctness.
Rule-based. No AI.
"""

from typing import List, Dict, Any
from .intent import GuardianIntent, IntentType, IntentPriority, ValidationResult


class IntentValidator:
    """Rule-based intent validator."""

    def validate(self, intent: GuardianIntent, all_intents: List[GuardianIntent]) -> ValidationResult:
        """Run all validations on an intent."""
        errors = []
        warnings = []

        # 1. Missing evidence
        if intent.evidence_count == 0 and intent.intent_type not in (IntentType.OBSERVE, IntentType.NO_ACTION):
            warnings.append(f"Missing evidence for {intent.intent_type.name} intent")

        # 2. Duplicate intent
        for existing in all_intents:
            if existing.intent_id == intent.intent_id:
                continue
            if (existing.intent_type == intent.intent_type
                and existing.source_assessment_id == intent.source_assessment_id
                and existing.status.name in ("PENDING", "ACTIVE")):
                warnings.append(f"Duplicate intent: {intent.intent_type.name} for assessment {intent.source_assessment_id}")

        # 3. Policy conflict
        if intent.intent_type == IntentType.NO_ACTION and intent.priority.value >= IntentPriority.HIGH.value:
            errors.append("Policy conflict: NO_ACTION with HIGH/URGENT priority")

        if intent.intent_type == IntentType.BLOCKED and intent.priority == IntentPriority.LOW:
            warnings.append("BLOCKED intent with LOW priority")

        # 4. Invalid priority
        if intent.intent_type == IntentType.ESCALATE and intent.priority.value < IntentPriority.HIGH.value:
            warnings.append("ESCALATE intent should have HIGH/URGENT priority")

        # 5. Invalid confidence
        if intent.confidence < 0 or intent.confidence > 100:
            errors.append(f"Invalid confidence: {intent.confidence}")

        # 6. Expired assessment (timestamp too old — >1 hour)
        import time
        age = time.time() - intent.timestamp
        if age > 3600 and intent.status.name == "PENDING":
            warnings.append(f"Expired assessment: intent age {age:.0f}s > 3600s")

        # 7. Orphan assessment
        if not intent.source_assessment_id and not intent.source_situation_id:
            warnings.append("Orphan intent: no source assessment or situation")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_batch(self, intents: List[GuardianIntent]) -> Dict[str, Any]:
        """Validate a batch of intents."""
        results = []
        all_valid = True
        for intent in intents:
            result = self.validate(intent, intents)
            results.append(result)
            if not result.valid:
                all_valid = False
        return {"all_valid": all_valid, "results": [r.to_dict() for r in results]}
