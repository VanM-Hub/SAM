"""
Guardian Package Validator.

Validates DecisionPackage completeness and consistency.
Rule-based. Deterministic. No AI.
"""

from typing import List
from dataclasses import dataclass, field

from .decision_package import DecisionPackage


@dataclass(frozen=True)
class PackageValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict:
        return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class PackageValidator:
    """Validates DecisionPackage completeness."""

    REQUIRED_SECTIONS = {"decision_input", "justification"}

    def validate(self, package: DecisionPackage) -> PackageValidationResult:
        errors = []; warnings = []

        # Missing sections
        missing = self.REQUIRED_SECTIONS - set(package.sections.keys())
        if missing:
            errors.append(f"Missing sections: {missing}")

        # Empty sections
        if package.total_sections == 0:
            warnings.append("Package has no sections")

        # Missing metadata
        if package.metadata is None:
            errors.append("Missing package metadata")

        # Missing IDs
        if not package.decision_input_id:
            warnings.append("No decision_input_id")
        if not package.justification_id:
            warnings.append("No justification_id")

        # Invalid version
        if package.metadata:
            if package.metadata.version not in ("1.0",):
                warnings.append(f"Unknown version: {package.metadata.version}")

        valid = len(errors) == 0
        score = max(0.0, 1.0 - (len(errors) * 0.4 + len(warnings) * 0.1))
        return PackageValidationResult(valid=valid, errors=errors, warnings=warnings, score=round(score, 2))
