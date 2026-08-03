"""NegotiationResult — result of version negotiation.

Per CONTRACT_SPEC 'Version Negotiation':
    - Both Citizens SHALL agree on a single version
    - Compatible version SHALL be chosen
    - Preference to non-deprecated versions
    - If no compatible version exists → negotiation fails
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NegotiationStatus(str, Enum):
    """Status of version negotiation."""
    RESOLVED = "RESOLVED"               # Single version agreed
    DEPRECATED_ONLY = "DEPRECATED_ONLY"  # Only deprecated versions available
    NO_INTERSECTION = "NO_INTERSECTION"  # No common versions
    NO_COMPATIBLE = "NO_COMPATIBLE"     # Common versions but none compatible
    FAILED = "FAILED"                   # General negotiation failure


@dataclass(frozen=True)
class NegotiationResult:
    """Result of version negotiation between two parties.

    Immutable — deterministic output.
    """
    status: NegotiationStatus
    negotiated_contract_id: Optional[str] = None
    negotiated_version: Optional[str] = None
    reason: str = ""
    candidate_versions: list = field(default_factory=list)

    def is_success(self) -> bool:
        """Negotiation produced an agreed version."""
        return self.status in (NegotiationStatus.RESOLVED, NegotiationStatus.DEPRECATED_ONLY)

    def is_failed(self) -> bool:
        """Negotiation failed — no version agreed."""
        return self.status in (
            NegotiationStatus.NO_INTERSECTION,
            NegotiationStatus.NO_COMPATIBLE,
            NegotiationStatus.FAILED,
        )

    @classmethod
    def resolved(
        cls,
        contract_id: str,
        version: str,
        reason: str = "",
    ) -> "NegotiationResult":
        """Create a successfully resolved result."""
        return cls(
            status=NegotiationStatus.RESOLVED,
            negotiated_contract_id=contract_id,
            negotiated_version=version,
            reason=reason or f"Agreed on version {version}",
        )

    @classmethod
    def deprecated_only(
        cls,
        contract_id: str,
        version: str,
    ) -> "NegotiationResult":
        """Create a deprecated-only result."""
        return cls(
            status=NegotiationStatus.DEPRECATED_ONLY,
            negotiated_contract_id=contract_id,
            negotiated_version=version,
            reason=f"Only deprecated version {version} available",
        )

    @classmethod
    def no_intersection(cls) -> "NegotiationResult":
        """Create a no-intersection result."""
        return cls(
            status=NegotiationStatus.NO_INTERSECTION,
            reason="No common versions between parties",
        )

    @classmethod
    def no_compatible(cls, reason: str = "") -> "NegotiationResult":
        """Create a no-compatible result."""
        return cls(
            status=NegotiationStatus.NO_COMPATIBLE,
            reason=reason or "Common versions exist but none are compatible",
        )

    def __repr__(self) -> str:
        return (
            f"NegotiationResult("
            f"status={self.status.value}, "
            f"version={self.negotiated_version}, "
            f"reason='{self.reason}')"
        )
