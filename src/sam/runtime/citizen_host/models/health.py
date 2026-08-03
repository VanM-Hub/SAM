"""Citizen Host health models — HealthStatus.

R9: Expose health.
The Runtime must always be able to report its health status.

Authority: GOVERNANCE Runtime Governance
Source: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
"""

from enum import Enum, auto


class HealthStatus(Enum):
    """Health status of the Runtime.

    States:
        AVAILABLE    — Runtime is fully operational.
        DEGRADED     — Runtime is operational but with reduced capability.
        UNAVAILABLE  — Runtime is not operational.

    Authority: GOVERNANCE
    """

    AVAILABLE = auto()
    """Full operational capability. All services responsive."""

    DEGRADED = auto()
    """Reduced capability. Some services may be unavailable."""

    UNAVAILABLE = auto()
    """Not operational. Runtime cannot serve requests."""

    def is_operational(self) -> bool:
        """Check if the Runtime can serve requests.

        Returns:
            True if AVAILABLE or DEGRADED, False if UNAVAILABLE.
        """
        return self in (HealthStatus.AVAILABLE, HealthStatus.DEGRADED)

    def is_fully_operational(self) -> bool:
        """Check if the Runtime is at full capacity.

        Returns:
            True only if AVAILABLE.
        """
        return self is HealthStatus.AVAILABLE
