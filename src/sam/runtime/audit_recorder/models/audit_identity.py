"""Audit Identity model — AUDIT_SPEC §Audit Identity.

Every Audit Record possesses a distinct identity with:
- audit_id: global identifier
- execution_reference: reference to Execution that produced the activity
- approval_reference: reference to Approval that authorized
- contract_reference: reference to Contract governing the activity
- capability_reference: reference to Capability involved
- citizen_reference: reference to Citizen context
- timestamp: when the activity occurred
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AuditIdentity:
    """Immutable identity for an Audit Record.

    Authority: AUDIT_SPEC L57-L69
    """
    audit_id: str
    execution_reference: str
    approval_reference: str
    contract_reference: str
    capability_reference: str
    citizen_reference: str
    timestamp: str

    def validate(self):
        """Validate all required fields are non-empty.

        Returns:
            True if all fields are non-empty and non-whitespace.

        Raises:
            ValueError: if any required field is empty.
        """
        errors = []
        if not self.audit_id or not self.audit_id.strip():
            errors.append("audit_id is required")
        if not self.execution_reference or not self.execution_reference.strip():
            errors.append("execution_reference is required")
        if not self.approval_reference or not self.approval_reference.strip():
            errors.append("approval_reference is required")
        if not self.contract_reference or not self.contract_reference.strip():
            errors.append("contract_reference is required")
        if not self.capability_reference or not self.capability_reference.strip():
            errors.append("capability_reference is required")
        if not self.citizen_reference or not self.citizen_reference.strip():
            errors.append("citizen_reference is required")
        if not self.timestamp or not self.timestamp.strip():
            errors.append("timestamp is required")
        if errors:
            raise ValueError("; ".join(errors))
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Return identity as a dictionary."""
        return {
            "audit_id": self.audit_id,
            "execution_reference": self.execution_reference,
            "approval_reference": self.approval_reference,
            "contract_reference": self.contract_reference,
            "capability_reference": self.capability_reference,
            "citizen_reference": self.citizen_reference,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"AuditIdentity("
            f"id='{self.audit_id}', "
            f"exec='{self.execution_reference}', "
            f"approval='{self.approval_reference}', "
            f"contract='{self.contract_reference}', "
            f"cap='{self.capability_reference}', "
            f"citizen='{self.citizen_reference}')"
        )
