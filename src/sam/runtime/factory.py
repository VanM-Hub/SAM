"""Capability Factory for SAM Framework.

This module provides a factory to lazily instantiate capability classes
from their descriptors. The factory has no dependency on Runtime or Registry,
only on models and SDK base classes.
"""

import importlib
from typing import Optional

import structlog

from sam.models import CapabilityDescriptor
from sam.sdk.base import Capability


logger = structlog.get_logger(__name__)


class CapabilityFactory:
    """Factory for creating capability instances from descriptors.

    The factory uses importlib to dynamically load the capability class
    specified in the descriptor's implementation path.
    """

    async def create(self, descriptor: CapabilityDescriptor) -> Capability:
        """Create a capability instance from its descriptor.

        Args:
            descriptor: CapabilityDescriptor containing the implementation path.

        Returns:
            An instance of the capability class.

        Raises:
            ImportError: If the module or class cannot be imported.
            AttributeError: If the class is not found in the module.
            TypeError: If the class does not inherit from Capability.
        """
        implementation = descriptor.implementation
        logger.info(
            "Creating capability instance",
            capability_id=descriptor.id,
            implementation=implementation,
        )

        try:
            # Split module path and class name
            # e.g., "sam.capabilities.health_checks.HealthCheckCapability"
            # -> module: "sam.capabilities.health_checks", class: "HealthCheckCapability"
            if "." not in implementation:
                raise ImportError(
                    f"Invalid implementation path '{implementation}': "
                    "must be 'module.path.ClassName'"
                )

            module_path, class_name = implementation.rsplit(".", 1)

            # Import the module
            logger.debug("Importing module", module=module_path, class_name=class_name)
            module = importlib.import_module(module_path)

            # Get the class
            cap_class = getattr(module, class_name, None)
            if cap_class is None:
                raise AttributeError(
                    f"Class '{class_name}' not found in module '{module_path}'"
                )

            # Verify it's a Capability subclass
            if not issubclass(cap_class, Capability):
                raise TypeError(
                    f"Class '{class_name}' does not inherit from Capability base class"
                )

            # Instantiate
            instance = cap_class()
            logger.info(
                "Capability instance created",
                capability_id=descriptor.id,
                class_name=class_name,
            )
            return instance

        except (ImportError, AttributeError, TypeError) as e:
            logger.error(
                "Failed to create capability",
                capability_id=descriptor.id,
                implementation=implementation,
                error=str(e),
            )
            raise ImportError(
                f"Failed to create capability '{descriptor.id}' "
                f"from '{implementation}': {e}"
            ) from e

    async def create_from_id(
        self, registry, capability_id: str
    ) -> Optional[Capability]:
        """Create a capability instance by looking up its descriptor in the registry.

        This is a convenience method for integration with the registry.

        Args:
            registry: CapabilityRegistry instance with registered descriptors.
            capability_id: The ID of the capability to create.

        Returns:
            Capability instance, or None if not found.

        Raises:
            ImportError: If instantiation fails.
        """
        # This assumes the registry has a method to get descriptor by ID
        # Adjust based on actual registry API
        descriptor = getattr(registry, "get_descriptor", None)
        if descriptor is None:
            logger.warning(
                "Registry does not support get_descriptor",
                capability_id=capability_id,
            )
            return None

        cap_descriptor = descriptor(capability_id)
        if cap_descriptor is None:
            logger.warning(
                "Descriptor not found in registry",
                capability_id=capability_id,
            )
            return None

        return await self.create(cap_descriptor)