"""CompatibilityResult — result of compatibility verification.

Per CONTRACT_SPEC 'Compatibility Rules':
    - Backward compatible: older consumer works with newer
    - Forward compatible: newer consumer works with older
    - Breaking change: breaks backward or forward
    - Compatible change: preserves compatibility
    - Deprecated contract: still defined but not preferred
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class CompatibilityStatus(str, Enum):
    """Status of a compatibility check."""
    COMPATIBLE = "COMPATIBLE"        # Versions are compatible
    BACKWARD_ONLY = "BACKWARD_ONLY"  # Only backward compatible
    BREAKING = "BREAKING"            # Incompatible — breaking change
    UNKNOWN = "UNKNOWN"              # Cannot determine (missing predecessor info)


@dataclass(frozen=True)
class CompatibilityResult:
    """Result of compatibility verification between two Contract versions.

    Immutable — deterministic output.
    """
    status: CompatibilityStatus
    is_compatible: bool
    backward_compatible: bool = True
    forward_compatible: bool = True
    breaking_changes: List[str] = field(default_factory=list)
    reason: str = ""
    predecessor_id: Optional[str] = None
    successor_id: Optional[str] = None

    @classmethod
    def compatible(
        cls,
        predecessor_id: Optional[str] = None,
        successor_id: Optional[str] = None,
    ) -> "CompatibilityResult":
        """Create a fully compatible result."""
        return cls(
            status=CompatibilityStatus.COMPATIBLE,
            is_compatible=True,
            backward_compatible=True,
            forward_compatible=True,
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            reason="Versions are fully compatible",
        )

    @classmethod
    def breaking(
        cls,
        changes: List[str],
        predecessor_id: Optional[str] = None,
        successor_id: Optional[str] = None,
    ) -> "CompatibilityResult":
        """Create a breaking change result."""
        return cls(
            status=CompatibilityStatus.BREAKING,
            is_compatible=False,
            backward_compatible=False,
            forward_compatible=False,
            breaking_changes=changes,
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            reason=f"Breaking changes: {', '.join(changes)}",
        )

    @classmethod
    def unknown(cls, reason: str = "") -> "CompatibilityResult":
        """Create an unknown compatibility result."""
        return cls(
            status=CompatibilityStatus.UNKNOWN,
            is_compatible=False,
            reason=reason or "Compatibility cannot be determined",
        )

    def __repr__(self) -> str:
        return f"CompatibilityResult(status={self.status.value}, reason='{self.reason}')"
