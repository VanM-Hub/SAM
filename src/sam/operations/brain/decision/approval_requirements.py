"""
Approval Requirements Engine.

Builds requirement sets for approval.
Rule-based. Deterministic.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field

from .approval_preparation import ApprovalRequirement


@dataclass(frozen=True)
class ApprovalRequirementSet:
    mandatory: List[str] = field(default_factory=list)
    recommended: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    blocked: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]:
        return {"mandatory":list(self.mandatory),"recommended":list(self.recommended),"optional":list(self.optional),
                "missing":list(self.missing),"blocked":list(self.blocked)}


class ApprovalRequirementsEngine:
    """Builds approval requirement sets."""

    def build(self, requirements: List[ApprovalRequirement]) -> ApprovalRequirementSet:
        mandatory = [r.name for r in requirements if r.category == "mandatory"]
        recommended = [r.name for r in requirements if r.category == "recommended"]
        optional = [r.name for r in requirements if r.category == "optional"]
        missing = [r.name for r in requirements if not r.satisfied]
        blocked = [r.name for r in requirements if not r.satisfied and r.category == "mandatory"]

        return ApprovalRequirementSet(
            mandatory=mandatory,
            recommended=recommended,
            optional=optional,
            missing=missing,
            blocked=blocked,
        )
