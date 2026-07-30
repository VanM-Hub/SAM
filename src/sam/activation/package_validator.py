"""Package Validator — validasi paket sebelum readiness."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_package import ActivationPackage


@dataclass(frozen=True)
class PackageValidation:
    package_id: str = ""
    valid: bool = False
    has_candidates: bool = False
    has_strategy: bool = False
    has_sequence: bool = False
    confidence_ok: bool = False
    errors: List[str] = field(default_factory=list)


class PackageValidator:
    """Memvalidasi ActivationPackage."""

    def validate(self, package: ActivationPackage) -> PackageValidation:
        errors: List[str] = []
        if not package.package_id:
            errors.append("No package ID")
        if not package.candidate_refs:
            errors.append("No candidates in package")
        if not package.strategy_ref:
            errors.append("No strategy reference")
        if not package.sequence_ref:
            errors.append("No sequence reference")
        if package.confidence <= 0:
            errors.append("Confidence <= 0")

        return PackageValidation(
            package_id=package.package_id,
            valid=len(errors) == 0 and package.total_candidates > 0,
            has_candidates=len(package.candidate_refs) > 0,
            has_strategy=bool(package.strategy_ref),
            has_sequence=bool(package.sequence_ref),
            confidence_ok=package.confidence > 0,
            errors=errors,
        )
