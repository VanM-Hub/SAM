"""Resolution Result models.

ResolutionResult captures the outcome of ADR-002 resolution.

Authority: ADR-002 Decision | REGISTRY_SPEC L143-L160
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ResolutionStatus(Enum):
    """The status of a capability resolution.

    Values:
        FOUND: An exact or compatible match was found.
        NOT_FOUND: No capability matches the requested identity.
        VERSION_MISMATCH: Identity matches but version is incompatible (major differs).
        DEPRECATED_ONLY: Only deprecated capabilities are available.
    """

    FOUND = auto()
    NOT_FOUND = auto()
    VERSION_MISMATCH = auto()
    DEPRECATED_ONLY = auto()


@dataclass(frozen=True)
class ResolutionResult:
    """The resolved result of a Capability Request.

    Immutable — same request + same registry = same result.

    Attributes:
        status: The resolution status.
        descriptor: The resolved capability (if FOUND or DEPRECATED_ONLY).
        reason: Human-readable reason for the result.
    """

    status: ResolutionStatus
    """The resolution status."""

    descriptor: Optional[object] = None
    """The resolved capability (RegistryEntry if available)."""

    reason: str = ""
    """Human-readable reason/summary for this result."""

    def is_success(self) -> bool:
        """Check if resolution produced a usable result.

        Returns:
            True for FOUND or DEPRECATED_ONLY.
        """
        return self.status in (
            ResolutionStatus.FOUND,
            ResolutionStatus.DEPRECATED_ONLY,
        )

    def is_fatal(self) -> bool:
        """Check if resolution failed fatally.

        Returns:
            True for NOT_FOUND or VERSION_MISMATCH.
        """
        return self.status in (
            ResolutionStatus.NOT_FOUND,
            ResolutionStatus.VERSION_MISMATCH,
        )
