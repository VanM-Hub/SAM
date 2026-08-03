"""Declaration validation.

Validates that a CapabilityDeclaration is complete and structurally
valid before publication.

Authority: CAPABILITY_SPEC | R5-001 §2.2
"""

import re
from typing import List, Set

from sam.runtime.capability_manager.models.declaration import (
    CapabilityDeclaration,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidDeclaration,
)


class DeclarationValidator:
    """Validates CapabilityDeclaration completeness.

    Checks:
        - Required fields: identity, name, version.
        - Identity format: no implementation names.
        - Version format: Major.Minor.Patch.
    """

    # ── Semantic version pattern ───────────────────────────────────

    _VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
    """Major.Minor.Patch format."""

    # ── Forbidden identity patterns ─────────────────────────────────

    _FORBIDDEN_PATTERNS: Set[str] = {
        "openai", "anthropic", "claude", "gpt", "grok", "gemini",
        "llama", "mistral", "cohere", "bedrock",
    }

    def validate(self, declaration: CapabilityDeclaration) -> bool:
        """Validate declaration completeness and correctness.

        Args:
            declaration: The CapabilityDeclaration to validate.

        Returns:
            True if valid.

        Raises:
            InvalidDeclaration: If validation fails.
        """
        errors: List[str] = []

        # Required fields
        if not declaration.identity or not declaration.identity.strip():
            errors.append("Capability identity must be non-empty.")
        if not declaration.name or not declaration.name.strip():
            errors.append("Capability name must be non-empty.")
        if not declaration.version or not declaration.version.strip():
            errors.append("Capability version must be non-empty.")

        # Identity format
        identity_lower = declaration.identity.lower()
        for pattern in self._FORBIDDEN_PATTERNS:
            if pattern in identity_lower:
                errors.append(
                    f"Identity '{declaration.identity}' contains "
                    f"implementation name '{pattern}'."
                )

        # Version format
        if declaration.version and not self._VERSION_PATTERN.match(
            declaration.version
        ):
            errors.append(
                f"Version '{declaration.version}' does not match "
                f"Major.Minor.Patch format (e.g. '1.0.0')."
            )

        if errors:
            raise InvalidDeclaration(
                message="; ".join(errors)
            )

        return True
