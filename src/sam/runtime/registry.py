"""Capability registry for storing and retrieving capability descriptors.

This registry is a lightweight catalog of capability metadata (CapabilityDescriptor).
It does NOT store instances or executors — those are created lazily by CapabilityFactory.
"""

from typing import Dict, List, Optional

import structlog

from sam.models import CapabilityDescriptor


logger = structlog.get_logger(__name__)


class CapabilityRegistry:
    """In-memory registry of capability descriptors.

    Capabilities are identified by their ``id`` (a string like "openclaw.health-checks").
    The registry supports registration, retrieval, listing, and removal of descriptors.
    """

    def __init__(self) -> None:
        self._descriptors: Dict[str, CapabilityDescriptor] = {}
        # Backwards-compatible alias for older tests/code that expect _capabilities
        # Keep both names pointing at the same dict to avoid divergence.
        self._capabilities = self._descriptors
        self.logger = logger.bind(component="CapabilityRegistry")

    async def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a capability descriptor.

        If a descriptor with the same ``id`` already exists,
        it will be overwritten after logging a warning.
        """
        cap_id = descriptor.id

        if cap_id in self._descriptors:
            self.logger.warning(
                "Overwriting existing capability descriptor",
                capability_id=cap_id,
            )

        self._descriptors[cap_id] = descriptor
        self.logger.info(
            "Capability descriptor registered",
            capability_id=cap_id,
            version=descriptor.version,
            implementation=descriptor.implementation,
            capability_type=descriptor.capability_type,
            risk_level=descriptor.risk_level,
        )

    async def get_descriptor(self, capability_id: str) -> Optional[CapabilityDescriptor]:
        """Retrieve a capability descriptor by its ID.

        Returns:
            The CapabilityDescriptor if found, None otherwise.
        """
        descriptor = self._descriptors.get(capability_id)
        if descriptor is not None:
            self.logger.debug(
                "Descriptor retrieved",
                capability_id=capability_id,
            )
        else:
            self.logger.warning(
                "Descriptor not found",
                capability_id=capability_id,
            )
        return descriptor

    async def list_descriptors(self) -> List[CapabilityDescriptor]:
        """Return all registered capability descriptors."""
        descriptors = list(self._descriptors.values())
        self.logger.debug(
            "Descriptors listed",
            count=len(descriptors),
        )
        return descriptors

    async def unregister(self, capability_id: str) -> None:
        """Remove a capability descriptor by its ID."""
        if capability_id in self._descriptors:
            del self._descriptors[capability_id]
            self.logger.info(
                "Capability descriptor unregistered",
                capability_id=capability_id,
            )
        else:
            self.logger.warning(
                "Attempt to unregister non-existent descriptor",
                capability_id=capability_id,
            )

    async def clear(self) -> None:
        """Remove all descriptors (mainly for testing)."""
        count = len(self._descriptors)
        self._descriptors.clear()
        self.logger.info(
            "Registry cleared",
            removed_count=count,
        )