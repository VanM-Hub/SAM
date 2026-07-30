"""
Approval Adapter.

Validates and finalizes approval envelopes.
Does NOT submit, approve, or reject. Preview only.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import uuid
from datetime import datetime

from .approval_envelope import ApprovalRequestEnvelope


@dataclass(frozen=True)
class ApprovalAdapterResult:
    success: bool = False; envelope_id: str = ""
    validation_result: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]: return {"success":self.success,"envelope_id":self.envelope_id,
        "validation_result":self.validation_result,"warnings":list(self.warnings),"errors":list(self.errors)}


class ApprovalAdapter:
    """Validates and finalizes approval envelopes."""

    def process(self, envelope: ApprovalRequestEnvelope) -> ApprovalAdapterResult:
        """Process an envelope through the adapter."""
        errors = []; warnings = []

        # Validate envelope
        if not envelope.envelope_id:
            errors.append("Missing envelope ID")
        if not envelope.references:
            errors.append("Missing references")
        if not envelope.payload:
            errors.append("Missing payload")
        else:
            if not envelope.payload.action_type:
                warnings.append("No action type in payload")
            if envelope.payload.priority < 0:
                errors.append("Negative priority")
            if envelope.payload.confidence < 0 or envelope.payload.confidence > 100:
                errors.append("Invalid confidence")

        # Validate references
        if envelope.references:
            if not envelope.references.preparation_id:
                warnings.append("No preparation ID reference")
            if not envelope.references.plan_id:
                warnings.append("No plan ID reference")

        # Contract check
        if envelope.ready and not envelope.payload:
            errors.append("Marked ready but has no payload")
        if envelope.ready and envelope.payload and envelope.payload.requires_approval and not envelope.payload.runtime_ids:
            warnings.append("Requires approval but no runtime IDs specified")

        validation_result = {
            "valid": len(errors) == 0,
            "score": max(0, 1.0 - len(errors) * 0.3),
        }

        return ApprovalAdapterResult(
            success=len(errors) == 0,
            envelope_id=envelope.envelope_id,
            validation_result=validation_result,
            warnings=warnings,
            errors=errors,
        )
