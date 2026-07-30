"""
Intake Summary Builder.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from .intake_record import ApprovalIntakeRecord
from .intake_validator import ValidationResult


@dataclass(frozen=True)
class ApprovalIntakeSummary:
    readiness_score: float = 0.0
    findings: int = 0
    warnings: int = 0
    readiness: str = "UNKNOWN"
    certified: bool = False
    source: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"readiness_score":self.readiness_score,"findings":self.findings,
        "warnings":self.warnings,"readiness":self.readiness,"certified":self.certified,"source":self.source}


class IntakeSummaryBuilder:
    @staticmethod
    def build(record: ApprovalIntakeRecord, validation: ValidationResult) -> ApprovalIntakeSummary:
        rs = record.readiness_score
        readiness = "READY" if rs >= 0.8 else "NEEDS_REVIEW" if rs >= 0.5 else "BLOCKED"
        src = record.metadata.source.name if record.metadata else "UNKNOWN"
        return ApprovalIntakeSummary(
            readiness_score=rs,
            findings=len(validation.errors),
            warnings=len(validation.warnings),
            readiness=readiness,
            certified=record.certified,
            source=src,
        )
