"""
Decision Runtime Package Validator.

Validates IncomingDecisionPackage for completeness and consistency.
Rules-based. Deterministic. No AI.
"""

from typing import List
from dataclasses import dataclass, field

from .package_protocol import IncomingDecisionPackage


@dataclass(frozen=True)
class DecisionPackageValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict:
        return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class PackageValidator:
    """Validates IncomingDecisionPackage integrity."""

    def validate(self, package: IncomingDecisionPackage) -> DecisionPackageValidationResult:
        errors = []; warnings = []

        # Required sections
        if not package.header:
            errors.append("Missing package header")
        if not package.body:
            errors.append("Missing package body")

        # Schema check
        if package.header:
            if not package.header.source_package_id:
                warnings.append("No source package ID")
            if package.header.total_sections == 0:
                warnings.append("Package has no sections")

        # Version
        if package.header and package.header.version not in ("1.0",):
            warnings.append(f"Unknown version: {package.header.version}")

        # References
        if package.header and not package.header.has_input:
            warnings.append("No decision input in package")
        if package.header and not package.header.has_justification:
            warnings.append("No justification in package")

        # Evidence
        body = package.body
        if body:
            if not body.decision_input and body.justification:
                warnings.append("Has justification but no decision input")

        # Integrity
        if body and body.decision_input:
            di = body.decision_input
            if "input_id" not in di:
                errors.append("Decision input missing input_id")
            if "timestamp" not in di:
                errors.append("Decision input missing timestamp")

        # Consistency
        if package.header and package.body:
            total = len(package.body.sections) if package.body else 0
            if total != package.header.total_sections:
                warnings.append(f"Section count mismatch: header={package.header.total_sections}, body={total}")

        valid = len(errors) == 0
        score = max(0.0, 1.0 - (len(errors) * 0.4 + len(warnings) * 0.1))
        return DecisionPackageValidationResult(valid=valid, errors=errors, warnings=warnings, score=round(score, 2))
