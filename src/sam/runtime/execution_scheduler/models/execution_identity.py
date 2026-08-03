"""Execution Identity model — EXECUTION_SPEC §Execution Identity.

Every Execution possesses a distinct identity with:
- execution_id: global identifier
- approval_reference: reference to Approval that authorized
- contract_reference: reference to Contract governing the operation
- capability_reference: reference to Capability being executed
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ExecutionIdentity:
    """Immutable identity for an Execution.

    Authority: EXECUTION_SPEC L73-L88
    """
    execution_id: str
    approval_reference: str
    contract_reference: str
    capability_reference: str

    def validate(self):
        """Validate all required fields are non-empty.

        Returns:
            True if all fields are non-empty and non-whitespace.

        Raises:
            ValueError: if any required field is empty.
        """
        errors = []
        if not self.execution_id or not self.execution_id.strip():
            errors.append("execution_id is required")
        if not self.approval_reference or not self.approval_reference.strip():
            errors.append("approval_reference is required")
        if not self.contract_reference or not self.contract_reference.strip():
            errors.append("contract_reference is required")
        if not self.capability_reference or not self.capability_reference.strip():
            errors.append("capability_reference is required")
        if errors:
            raise ValueError("; ".join(errors))
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Return identity as a dictionary."""
        return {
            "execution_id": self.execution_id,
            "approval_reference": self.approval_reference,
            "contract_reference": self.contract_reference,
            "capability_reference": self.capability_reference,
        }

    def __repr__(self) -> str:
        return (
            f"ExecutionIdentity("
            f"id='{self.execution_id}', "
            f"approval='{self.approval_reference}', "
            f"contract='{self.contract_reference}', "
            f"cap='{self.capability_reference}')"
        )
