"""
Intake Validator.

Validates ApprovalIntakeRecord integrity before processing.
"""

from dataclasses import dataclass, field
from typing import List
from .intake_record import ApprovalIntakeRecord


@dataclass(frozen=True)
class ValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),
        "warnings":list(self.warnings),"score":self.score}


class IntakeValidator:
    VALID_VERSION_PREFIXES = ("5.", "6.")

    def validate(self, record: ApprovalIntakeRecord) -> ValidationResult:
        errors = []; warnings = []

        if not record.record_id: errors.append("Missing record_id")
        if not record.decision_record_id: errors.append("Missing decision_record_id")
        if not record.pipeline_version: errors.append("Missing pipeline_version")
        elif not record.pipeline_version.startswith(self.VALID_VERSION_PREFIXES):
            warnings.append(f"Unexpected pipeline version: {record.pipeline_version}")
        if record.timestamp <= 0: errors.append("Invalid timestamp")
        if record.readiness_score < 0 or record.readiness_score > 1.0:
            errors.append("Readiness score out of range")

        meta = record.metadata
        if meta and meta.source.name not in ("MANUAL","DECISION_RUNTIME","API","SYSTEM"):
            warnings.append(f"Unknown source: {meta.source.name}")

        return ValidationResult(
            valid=len(errors)==0, errors=errors, warnings=warnings,
            score=max(0, 1 - len(errors)*0.3)
        )
