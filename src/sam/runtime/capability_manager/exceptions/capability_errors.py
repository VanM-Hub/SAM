"""Capability Manager domain exceptions.

Exception hierarchy for capability-related errors.
Designed for linear failure propagation toward Audit (ADR-004).

Authority: ADR-004 | R5-001 §2.2
"""


class CapabilityError(Exception):
    """Base exception for all Capability Manager errors.

    Authority: ADR-004
    """

    def __init__(self, message: str = "Capability operation failed") -> None:
        super().__init__(message)


class InvalidDeclaration(CapabilityError):
    """Raised when a CapabilityDeclaration fails validation.

    Possible causes:
        - Missing required fields (identity, name, version).
        - Identity contains implementation names.
        - Version format is invalid.
    """

    def __init__(self, message: str = "Invalid capability declaration") -> None:
        super().__init__(message)


class InvalidTransition(CapabilityError):
    """Raised when a lifecycle transition is not in the allowed path.

    Lifecycle transitions must follow:
    DECLARED → REGISTERED → CERTIFIED → AVAILABLE → DEPRECATED → RETIRED

    Deprecated may return to Available.
    Retired is terminal.
    """

    def __init__(
        self,
        current: str = "",
        target: str = "",
        message: str = "Invalid lifecycle transition",
    ) -> None:
        full = f"{message}: {current} → {target}" if current and target else message
        super().__init__(full)
        self.current = current
        self.target = target


class InvalidDescriptor(CapabilityError):
    """Raised when a CapabilityDescriptor fails integrity validation.

    Possible causes:
        - Missing required fields.
        - Inconsistent state.
        - Corrupted identity.
    """

    def __init__(self, message: str = "Invalid capability descriptor") -> None:
        super().__init__(message)


class DescriptorImmutable(CapabilityError):
    """Raised when attempting to modify an immutable descriptor.

    Once published (beyond DECLARED state), capability descriptors
    cannot be modified.
    """

    def __init__(
        self,
        identity: str = "",
        current_state: str = "",
    ) -> None:
        msg = (
            f"Capability descriptor '{identity}' is immutable "
            f"(current state: {current_state})"
            if identity
            else "Capability descriptor is immutable"
        )
        super().__init__(msg)
        self.identity = identity
        self.current_state = current_state


class CapabilityNotFound(CapabilityError):
    """Raised when a requested capability is not found.

    The capability may not exist or may have been retired.
    """

    def __init__(self, identity: str = "") -> None:
        msg = (
            f"Capability '{identity}' not found" if identity
            else "Capability not found"
        )
        super().__init__(msg)
        self.identity = identity


class CertificationFailed(CapabilityError):
    """Raised when a capability fails certification criteria.

    Certification verifies: descriptor integrity, contract validity,
    determinism, immutability, discoverability, governance compliance.
    """

    def __init__(
        self,
        identity: str = "",
        reason: str = "",
    ) -> None:
        msg = (
            f"Certification failed for '{identity}': {reason}"
            if identity and reason
            else "Certification failed"
        )
        super().__init__(msg)
        self.identity = identity
        self.reason = reason
