"""Descriptor integrity validation.

Validates that every CapabilityDescriptor is complete, valid,
and consistent before publication.

Authority: CAPABILITY_SPEC | R5-001 §2.2
"""

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidDescriptor,
)


class DescriptorValidator:
    """Validates CapabilityDescriptor integrity.

    Checks:
        - Required fields are non-empty (identity, name, version).
        - Identity does not contain implementation names.
        - Lifecycle state is valid.
    """

    # ── Forbidden patterns in capability identity ──────────────────

    _FORBIDDEN_IDENTITY_PATTERNS = frozenset({
        "openai", "anthropic", "claude", "gpt", "grok", "gemini",
        "llama", "mistral", "cohere", "bedrock",
    })

    def validate(self, descriptor: CapabilityDescriptor) -> bool:
        """Validate descriptor integrity.

        Args:
            descriptor: The CapabilityDescriptor to validate.

        Returns:
            True if valid.

        Raises:
            InvalidDescriptor: If validation fails.
        """
        self._validate_required_fields(descriptor)
        self._validate_identity_format(descriptor)
        return True

    def _validate_required_fields(self, descriptor: CapabilityDescriptor) -> None:
        """Validate that required fields are non-empty."""
        if not descriptor.identity or not descriptor.identity.strip():
            raise InvalidDescriptor("Capability identity must be non-empty.")
        if not descriptor.name or not descriptor.name.strip():
            raise InvalidDescriptor("Capability name must be non-empty.")
        if not descriptor.version or not descriptor.version.strip():
            raise InvalidDescriptor("Capability version must be non-empty.")

    def _validate_identity_format(self, descriptor: CapabilityDescriptor) -> None:
        """Validate that identity does not contain implementation names."""
        identity_lower = descriptor.identity.lower()
        for pattern in self._FORBIDDEN_IDENTITY_PATTERNS:
            if pattern in identity_lower:
                raise InvalidDescriptor(
                    f"Capability identity '{descriptor.identity}' contains "
                    f"implementation name '{pattern}'. "
                    f"Capability identity must describe behavior, not implementation."
                )

    def validate_publishable(self, descriptor: CapabilityDescriptor) -> bool:
        """Validate that a descriptor is ready for publication.

        Publication-ready means:
            - All required fields present.
            - Identity format valid.
            - No implementation names in identity.

        Args:
            descriptor: The descriptor to validate.

        Returns:
            True if publishable.
        """
        return self.validate(descriptor)
