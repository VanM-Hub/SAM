"""Registry Entry model.

RegistryEntry represents a capability stored in the registry
for discovery and resolution. It is the local representation
of a CapabilityDescriptor published by the Capability Manager.

Compatible with (but independent of) CapabilityDescriptor.

Authority: REGISTRY_SPEC | CAPABILITY_SPEC
"""

from dataclasses import dataclass


# Valid lifecycle states for registry entries
_VALID_STATES = frozenset({
    "DECLARED",
    "REGISTERED",
    "CERTIFIED",
    "AVAILABLE",
    "DEPRECATED",
    "RETIRED",
    "SUSPENDED",
    "REMOVED",
})


@dataclass(frozen=True)
class RegistryEntry:
    """An entry in the capability registry.

    Immutable — once registered, identity + version + state are bound.

    Attributes:
        identity: Unique capability identifier (e.g., 'memory.lookup').
        name: Human-readable capability name.
        version: Version in Major.Minor.Patch format.
        lifecycle_state: Current lifecycle state.
        contract_reference: Reference to the governing contract.
    """

    identity: str
    """Unique capability identifier."""

    name: str
    """Human-readable name."""

    version: str
    """Version in Major.Minor.Patch format."""

    lifecycle_state: str = "DECLARED"
    """Current lifecycle state (one of _VALID_STATES)."""

    contract_reference: str = ""
    """Reference to the governing contract."""

    def validate(self) -> bool:
        """Validate that all required fields are non-empty.

        Returns:
            True if identity, name, and version are non-empty.
        """
        return bool(
            self.identity.strip()
            and self.name.strip()
            and self.version.strip()
        )

    def is_discoverable(self) -> bool:
        """Check if this entry can be discovered.

        RETIRED capabilities are NOT discoverable.

        Returns:
            True if lifecycle_state is not RETIRED.
        """
        return self.lifecycle_state != "RETIRED"

    def is_deprecated(self) -> bool:
        """Check if this entry is deprecated.

        Returns:
            True if lifecycle_state is DEPRECATED.
        """
        return self.lifecycle_state == "DEPRECATED"

    def is_suspended_or_removed(self) -> bool:
        """Check if this entry is suspended or removed.

        Per REGISTRY_SPEC L146, suspended/removed objects
        are NOT candidates for resolution.

        Returns:
            True if lifecycle_state is SUSPENDED or REMOVED.
        """
        return self.lifecycle_state in ("SUSPENDED", "REMOVED")

    def is_not_candidate(self) -> bool:
        """Check if this entry should be excluded from candidate selection.

        Returns:
            True if suspended/removed (REGISTRY_SPEC L146).
        """
        return self.is_suspended_or_removed()

    def major_version(self) -> int:
        """Extract major version component.

        Returns:
            Major version as integer. 0 if unparseable.
        """
        try:
            return int(self.version.split(".")[0])
        except (ValueError, IndexError):
            return 0

    def __repr__(self) -> str:
        return (
            f"RegistryEntry(identity='{self.identity}', "
            f"version='{self.version}', "
            f"state='{self.lifecycle_state}')"
        )
