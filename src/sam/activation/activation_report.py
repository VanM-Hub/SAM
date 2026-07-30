"""Activation Report — laporan validasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_validator import ValidationReport
from sam.activation.activation_constraints import ConstraintResult
from sam.activation.activation_readiness import ReadinessCheck


@dataclass(frozen=True)
class ActivationReport:
    report_id: str = ""
    valid: bool = False
    validation: Optional[ValidationReport] = None
    constraints: List[ConstraintResult] = field(default_factory=list)
    readiness: List[ReadinessCheck] = field(default_factory=list)
    ready_score: float = 0.0
    summary: str = ""


class ActivationReportBuilder:
    """Membangun ActivationReport dari berbagai komponen."""

    def build(self, report_id: str, validation: ValidationReport,
              constraints: List[ConstraintResult],
              readiness: List[ReadinessCheck]) -> ActivationReport:
        ready_score = sum(r.score for r in readiness) / len(readiness) if readiness else 0.0
        all_valid = validation.valid and all(c.passed for c in constraints) and ready_score >= 0.5
        return ActivationReport(
            report_id=report_id,
            valid=all_valid,
            validation=validation,
            constraints=constraints,
            readiness=readiness,
            ready_score=round(ready_score, 2),
            summary=f"Valid={all_valid}, Score={ready_score:.2f}",
        )
