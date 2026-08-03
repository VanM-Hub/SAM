"""Approval Request per APPROVAL_SPEC.

The conceptual input to the Approval process:
- Decision Context
- Referenced Contract
- Referenced Capability
- Referenced Citizen (optional)
"""

from dataclasses import dataclass
from typing import Optional

from src.sam.runtime.contracts import ContractIdentity


@dataclass(frozen=True)
class ApprovalRequest:
    """Approval Request — the conceptual input to the Approval process.

    Per APPROVAL_SPEC 'Approval Request':
    - Required: decision_context, contract_reference, capability_reference
    - Optional: citizen_reference, expires_at

    Frozen — requests are immutable once submitted.
    """
    decision_context: str
    contract_reference: ContractIdentity
    capability_reference: str
    requested_by: str
    citizen_reference: Optional[str] = None
    expires_at: Optional[float] = None

    def validate(self) -> bool:
        """Basic field presence check."""
        if not self.decision_context.strip():
            return False
        if not self.capability_reference.strip():
            return False
        if not self.requested_by.strip():
            return False
        if not self.contract_reference.validate():
            return False
        return True

    def is_expired(self) -> bool:
        """Check whether the request has expired.

        Returns True if expires_at is set and has passed.
        None expires_at means the request never expires.
        """
        if self.expires_at is None:
            return False
        import time
        return time.time() > self.expires_at

    def __repr__(self) -> str:
        return (
            f"ApprovalRequest("
            f"ctx='{self.decision_context[:20]}', "
            f"cap='{self.capability_reference}', "
            f"by='{self.requested_by}')"
        )
