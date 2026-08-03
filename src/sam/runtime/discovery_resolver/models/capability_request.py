"""Capability Request model.

A Capability Request is the sole input to discovery/resolution.
No implicit context — only identity, requested version, and requester.

Authority: REGISTRY_SPEC Discovery Protocol | ADR-002 D-17
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityRequest:
    """A request to discover and resolve a Capability.

    Immutable — the same request always resolves to the same result
    (determinism guarantee per ADR-002 and REGISTRY_SPEC L147/L149).

    Attributes:
        identity: The capability identity to resolve (e.g., 'memory.lookup').
        requested_version: The target version in Major.Minor.Patch format.
        requester: The requesting entity identifier.
    """

    identity: str
    """The capability identity to resolve — must be non-empty."""

    requested_version: str
    """The target version in semver format — must be non-empty."""

    requester: str
    """The requesting entity — must be non-empty."""

    def validate(self) -> bool:
        """Validate that all required fields are non-empty.

        Returns:
            True if all required fields have content.
        """
        return bool(
            self.identity.strip()
            and self.requested_version.strip()
            and self.requester.strip()
        )

    def major_version(self) -> int:
        """Extract major version from requested_version.

        Returns:
            The major version component as integer.
            0 if version cannot be parsed.
        """
        try:
            return int(self.requested_version.split(".")[0])
        except (ValueError, IndexError):
            return 0
