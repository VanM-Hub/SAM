"""Registry entry validator.

Validates registry entries for consistency and completeness.

Authority: REGISTRY_SPEC
"""

from sam.runtime.discovery_resolver.models.registry_entry import (
    RegistryEntry,
    _VALID_STATES,
)
from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    InvalidRegistryEntry,
)


class RegistryValidator:
    """Validates RegistryEntry structure and content."""

    def validate(self, entry: RegistryEntry) -> bool:
        """Validate a registry entry.

        Checks:
            - Non-empty identity
            - Non-empty name
            - Non-empty version
            - Valid lifecycle state

        Args:
            entry: The RegistryEntry to validate.

        Returns:
            True if valid.

        Raises:
            InvalidRegistryEntry: If any validation fails.
        """
        if not entry.identity.strip():
            raise InvalidRegistryEntry(
                "Registry entry identity is required"
            )
        if not entry.name.strip():
            raise InvalidRegistryEntry(
                "Registry entry name is required"
            )
        if not entry.version.strip():
            raise InvalidRegistryEntry(
                "Registry entry version is required"
            )
        if entry.lifecycle_state not in _VALID_STATES:
            raise InvalidRegistryEntry(
                f"Invalid lifecycle state: '{entry.lifecycle_state}'. "
                f"Must be one of: {sorted(_VALID_STATES)}"
            )
        return True
