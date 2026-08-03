"""Capability publication service.

Handles the full publication flow:
1. Validate declaration.
2. Create immutable CapabilityDescriptor.
3. Store in managed registry.

Authority: CAPABILITY_SPEC | R5-001 §2.2 | I0-001 §2.2
"""

from typing import Dict

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.models.declaration import (
    CapabilityDeclaration,
)
from sam.runtime.capability_manager.interfaces.manager_interface import (
    PublishResult,
)
from sam.runtime.capability_manager.validation.declaration_validator import (
    DeclarationValidator,
)
from sam.runtime.capability_manager.validation.descriptor_validator import (
    DescriptorValidator,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidDeclaration,
    InvalidDescriptor,
)


class PublicationService:
    """Orchestrates Capability publication.

    Flow:
        1. declaration_validator.validate(declaration)
        2. Build frozen CapabilityDescriptor
        3. descriptor_validator.validate_publishable(descriptor)
        4. Store in registry
        5. Return PublishResult
    """

    def __init__(
        self,
        declaration_validator: DeclarationValidator = None,
        descriptor_validator: DescriptorValidator = None,
    ) -> None:
        self._declaration_validator = (
            declaration_validator or DeclarationValidator()
        )
        self._descriptor_validator = (
            descriptor_validator or DescriptorValidator()
        )
        # In-memory capability store (registry access point)
        self._store: Dict[str, CapabilityDescriptor] = {}

    def publish(self, declaration: CapabilityDeclaration) -> PublishResult:
        """Validate and publish a capability declaration.

        Args:
            declaration: The CapabilityDeclaration to publish.

        Returns:
            PublishResult with the published descriptor.

        Raises:
            InvalidDeclaration: If declaration validation fails.
            InvalidDescriptor: If resulting descriptor is invalid.
        """
        # Step 1: Validate declaration
        self._declaration_validator.validate(declaration)

        # Step 2: Build immutable descriptor
        descriptor = self._build_descriptor(declaration)

        # Step 3: Validate resulting descriptor
        self._descriptor_validator.validate_publishable(descriptor)

        # Step 4: Store (identity must be unique)
        if descriptor.identity in self._store:
            raise InvalidDeclaration(
                f"Capability '{descriptor.identity}' already exists."
            )

        self._store[descriptor.identity] = descriptor

        # Step 5: Return result
        return PublishResult(
            descriptor=descriptor,
            success=True,
            detail=f"Capability '{descriptor.identity}' published successfully.",
        )

    def get(self, identity: str) -> CapabilityDescriptor:
        """Retrieve a capability from the store.

        Args:
            identity: Capability identity.

        Returns:
            The CapabilityDescriptor.

        Raises:
            KeyError: If not found.
        """
        return self._store[identity]

    def get_optional(self, identity: str):
        """Retrieve a capability, returning None if not found.

        Args:
            identity: Capability identity.

        Returns:
            CapabilityDescriptor or None.
        """
        return self._store.get(identity)

    def list_all(self):
        """Retrieve all stored capabilities.

        Returns:
            List of all CapabilityDescriptors.
        """
        return list(self._store.values())

    # ── Private ────────────────────────────────────────────────────

    def _build_descriptor(
        self,
        declaration: CapabilityDeclaration,
    ) -> CapabilityDescriptor:
        """Build a frozen CapabilityDescriptor from a declaration.

        The resulting descriptor starts in DECLARED state.
        """
        return CapabilityDescriptor(
            identity=declaration.identity,
            name=declaration.name,
            version=declaration.version,
            description=declaration.description,
            owner_citizen=declaration.owner_citizen,
            inputs=declaration.inputs,
            outputs=declaration.outputs,
            constraints=declaration.constraints,
            compatibility=declaration.compatibility,
            metadata=declaration.metadata,
        )
