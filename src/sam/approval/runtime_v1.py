"""
Approval Runtime V1 — Intake Runtime.

Independent entry point for Approval Runtime.
Receives FinalDecisionRecord and runs intake pipeline.
Does NOT auto-approve, auto-route, or auto-execute.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from .intake_record import ApprovalIntakeRecord, IntakeMetadata, IntakeSource
from .intake_validator import IntakeValidator, ValidationResult
from .intake_normalizer import IntakeNormalizer, NormalizedApprovalRecord
from .intake_registry import IntakeRegistry
from .intake_summary import IntakeSummaryBuilder, ApprovalIntakeSummary
from .conversation_intake import ConversationIntakeBridge
from .dashboard_intake import DashboardIntakeBridge


@dataclass(frozen=True)
class ApprovalRuntimeResult:
    success: bool = False; record_id: str = ""
    validation: Optional[ValidationResult] = None
    normalized: Optional[NormalizedApprovalRecord] = None
    summary: Optional[ApprovalIntakeSummary] = None
    error: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"success":self.success,"record_id":self.record_id,
        "validation":self.validation.to_dict() if self.validation else None,
        "normalized":self.normalized.to_dict() if self.normalized else None,
        "summary":self.summary.to_dict() if self.summary else None,"error":self.error}


class ApprovalRuntimeV1:
    def __init__(self) -> None:
        self._validator = IntakeValidator()
        self._normalizer = IntakeNormalizer()
        self._registry = IntakeRegistry()
        self._summary_builder = IntakeSummaryBuilder()

        self._last_validation: Optional[ValidationResult] = None
        self._last_summary: Optional[ApprovalIntakeSummary] = None
        self._last_normalized: Optional[NormalizedApprovalRecord] = None

        self._conversation = ConversationIntakeBridge(self)
        self._dashboard = DashboardIntakeBridge(self)

    @property
    def conversation(self): return self._conversation
    @property
    def dashboard(self): return self._dashboard

    def process(self, record: ApprovalIntakeRecord) -> ApprovalRuntimeResult:
        # Validate
        validation = self._validator.validate(record)
        self._last_validation = validation

        if not validation.valid:
            return ApprovalRuntimeResult(success=False, record_id=record.record_id,
                                          validation=validation, error="Validation failed")

        # Normalize
        normalized = self._normalizer.normalize(record)
        self._last_normalized = normalized

        # Register
        self._registry.register(record, normalized)

        # Summary
        summary = self._summary_builder.build(record, validation)
        self._last_summary = summary

        return ApprovalRuntimeResult(
            success=True,
            record_id=record.record_id,
            validation=validation,
            normalized=normalized,
            summary=summary,
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "version": "6.0.0",
            "intake_count": self._registry.count if self._registry else 0,
            "last_record_id": self._registry.latest.record_id if self._registry and self._registry.latest else None,
        }
