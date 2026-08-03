"""Citizen Host domain exceptions.

Exception hierarchy for boundary violations and access errors.
Designed for linear failure propagation toward Audit (ADR-004).

Authority: ADR-004 | ADR-006 | R4-001 §2.3
"""


class InvalidBoundaryAccess(Exception):
    """Raised when a request violates the Contracts + Registry boundary.

    ADR-006: All external access must come through Contracts + Registry.
    This exception is raised when a request attempts to bypass this boundary.

    Authority: ADR-006
    """

    def __init__(self, message: str = "Access boundary violation") -> None:
        super().__init__(message)
        self._boundary_type = "External"

    @property
    def boundary_type(self) -> str:
        """The type of boundary that was violated."""
        return self._boundary_type


class UnauthorizedEntryPoint(InvalidBoundaryAccess):
    """Raised when a request enters through an unauthorized entry point.

    Only Contracts + Registry are valid external entry points.

    Authority: ADR-006
    """

    def __init__(self, message: str = "Unauthorized entry point") -> None:
        super().__init__(message)
        self._boundary_type = "EntryPoint"


class DirectUnitAccess(InvalidBoundaryAccess):
    """Raised when a request attempts direct access to another unit.

    Lateral communication between units is forbidden (R5-001 B6).
    All interaction flows through the linear chain.

    Authority: R5-001 B6
    """

    def __init__(
        self,
        target_unit: str = "",
        message: str = "Direct unit access forbidden",
    ) -> None:
        full_message = (
            f"{message}: {target_unit}" if target_unit else message
        )
        super().__init__(full_message)
        self._boundary_type = "UnitIsolation"
        self.target_unit = target_unit


class HostNotOperational(InvalidBoundaryAccess):
    """Raised when a request arrives while the host is not operational.

    The host must be in RUNNING or DEGRADED state to accept requests.

    Authority: HostLifecycle
    """

    def __init__(self, current_state: str = "") -> None:
        message = (
            f"Citizen Host is not operational. Current state: {current_state}"
            if current_state
            else "Citizen Host is not operational"
        )
        super().__init__(message)
        self._boundary_type = "Operational"
        self.current_state = current_state
