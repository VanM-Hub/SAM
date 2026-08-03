"""Audit Record model — AUDIT_SPEC §Audit Record.

An Audit Record is the conceptual representation of an operational event.
It SHALL be able to reference:
- Identity: the Audit Identity of the record
- Context: the context in which the activity occurred
- References: Execution, Approval, Contract, Capability references
- Outcome: the conceptual outcome of the activity
- Timestamp: when the activity occurred
- Verification: verification status and evidence

An Audit Record is IMMUTABLE after creation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from .audit_identity import AuditIdentity
from .verification_result import VerificationResult


@dataclass(frozen=True)
class AuditRecord:
    """Immutable audit record representing an operational event.

    Authority: AUDIT_SPEC L72-L84

    Once created, the record cannot be modified. Verification
    produces a new VerificationResult that is attached to the
    record as metadata.
    """
    identity: AuditIdentity
    outcome: str
    outcome_message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    verification: Optional[VerificationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    failure_event: Optional[str] = None

    def __post_init__(self):
        """Post-init: identity validation is deferred to is_missing_reference().
        
        The record allows creation with incomplete references —
        traceability completeness is checked via is_missing_reference()
        and the traceability validator, not at construction time.
        """
        pass

    @property
    def audit_id(self) -> str:
        """Shortcut for identity.audit_id."""
        return self.identity.audit_id

    @property
    def execution_reference(self) -> str:
        """Shortcut for identity.execution_reference."""
        return self.identity.execution_reference

    @property
    def approval_reference(self) -> str:
        """Shortcut for identity.approval_reference."""
        return self.identity.approval_reference

    @property
    def contract_reference(self) -> str:
        """Shortcut for identity.contract_reference."""
        return self.identity.contract_reference

    @property
    def capability_reference(self) -> str:
        """Shortcut for identity.capability_reference."""
        return self.identity.capability_reference

    @property
    def citizen_reference(self) -> str:
        """Shortcut for identity.citizen_reference."""
        return self.identity.citizen_reference

    @property
    def timestamp(self) -> str:
        """Shortcut for identity.timestamp."""
        return self.identity.timestamp

    def is_verified(self) -> bool:
        """Return True if the record has a verification result."""
        return self.verification is not None

    def is_missing_reference(self) -> bool:
        """Check if any required traceability reference is missing.

        Per AUDIT_SPEC §Traceability Rules - all references must be present.
        """
        if self.identity is None:
            return True
        refs = [
            self.identity.execution_reference,
            self.identity.approval_reference,
            self.identity.contract_reference,
            self.identity.capability_reference,
            self.identity.citizen_reference,
        ]
        return any(not r or not r.strip() for r in refs)

    def to_dict(self) -> Dict[str, Any]:
        """Return record as a dictionary."""
        return {
            "audit_id": self.audit_id,
            "identity": self.identity.to_dict(),
            "outcome": self.outcome,
            "outcome_message": self.outcome_message,
            "context": self.context,
            "verification": (
                self.verification.to_dict() if self.verification else None
            ),
            "metadata": self.metadata,
            "failure_event": self.failure_event,
        }

    def __repr__(self) -> str:
        verified = "verified" if self.is_verified() else "not_verified"
        return (
            f"AuditRecord("
            f"id='{self.audit_id}', "
            f"outcome='{self.outcome}', "
            f"verification={verified})"
        )
