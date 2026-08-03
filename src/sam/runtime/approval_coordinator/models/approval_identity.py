"""Approval identity per APPROVAL_SPEC.

Every Approval possesses a distinct identity:
- Approval ID: global identifier
- Decision Context: the context of the authorization decision
- Contract Reference: reference to the governing Contract
- Capability Reference: reference to the Capability
- Citizen Reference: optional Citizen reference
"""

from dataclasses import dataclass
from typing import Optional

from src.sam.runtime.contracts import ContractIdentity


@dataclass(frozen=True)
class ApprovalIdentity:
    """Approval identity per APPROVAL_SPEC 'Approval Identity'.

    Frozen in accordance with the principle that approval identity is
    established at creation and must not be mutable.
    """
    approval_id: str
    decision_context: str
    contract_reference: ContractIdentity
    capability_reference: str
    citizen_reference: Optional[str] = None

    def validate(self) -> bool:
        """Basic field presence check.

        Returns True if all required fields are present and non-empty.
        """
        return bool(
            self.approval_id.strip()
            and self.decision_context.strip()
            and self.capability_reference.strip()
            and self.contract_reference.validate()
        )

    def __repr__(self) -> str:
        return (
            f"ApprovalIdentity("
            f"id='{self.approval_id}', "
            f"ctx='{self.decision_context[:20]}', "
            f"cap='{self.capability_reference}', "
            f"contract='{self.contract_reference.contract_id}')"
        )
