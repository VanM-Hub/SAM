"""Execution Request model — EXECUTION_SPEC §Execution Request.

Required input: Referenced Approval, Referenced Contract, Referenced Capability.
Optional input: Additional context required by Contract or Capability.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExecutionRequest:
    """Immutable request to create an Execution.

    Authority: EXECUTION_SPEC L94-L99
    """
    approval_reference: str
    contract_reference: str
    capability_reference: str
    context: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self):
        """Validate required fields are non-empty.

        Returns:
            True if all required fields are valid.

        Raises:
            ValueError: if any required field is empty or whitespace-only.
        """
        errors = []
        if not self.approval_reference or not self.approval_reference.strip():
            errors.append("approval_reference is required")
        if not self.contract_reference or not self.contract_reference.strip():
            errors.append("contract_reference is required")
        if not self.capability_reference or not self.capability_reference.strip():
            errors.append("capability_reference is required")
        if errors:
            raise ValueError("; ".join(errors))
        return True

    def __repr__(self) -> str:
        return (
            f"ExecutionRequest("
            f"approval='{self.approval_reference}', "
            f"contract='{self.contract_reference}', "
            f"cap='{self.capability_reference}')"
        )
