"""Discovery Resolver exception hierarchy.

Authority: I0-001 §2.3
"""


class ResolutionError(Exception):
    """Base exception for all Discovery Resolver errors."""
    pass


class InvalidRequest(ResolutionError):
    """The CapabilityRequest is malformed.

    Raised when required fields are empty or invalid.
    """
    pass


class RegistryEntryNotFound(ResolutionError):
    """The requested registry entry was not found.

    Raised by direct lookup when the entry identity is unknown.
    """
    pass


class InvalidRegistryEntry(ResolutionError):
    """The RegistryEntry is malformed.

    Raised when required fields are empty or lifecycle state is invalid.
    """
    pass


class ResolutionNotDeterministic(ResolutionError):
    """Resolution produced different results for the same input.

    This indicates a determinism contract violation
    (REGISTRY_SPEC L147/L149, ADR-002, Art. VII).
    """
    pass


class InvalidTransition(ResolutionError):
    """An illegal lifecycle state transition was attempted."""
    pass


class ResolverNotOperational(ResolutionError):
    """Resolution or registration attempted when resolver is not RUNNING."""
    pass
