"""Capability discovery from knowledge documents.

This module discovers capability descriptors from knowledge documents
and registers them with the CapabilityRegistry.
"""

from typing import List, Optional, Set

import structlog

from sam.models import CapabilityDescriptor
from sam.knowledge.loader import KnowledgeLoader
from sam.runtime.registry import CapabilityRegistry
from sam.validation import (
    ValidationError,
    validate_and_build_descriptor,
    validate_capability_metadata,
)


class CapabilityDiscovery:
    """Discovers capability descriptors from knowledge documents and registers them."""

    def __init__(self, registry: CapabilityRegistry, loader: KnowledgeLoader) -> None:
        self.registry = registry
        self.loader = loader
        self.logger = structlog.get_logger(__name__)

    async def discover(self) -> List[str]:
        """Discover and register capability descriptors from knowledge documents.

        Returns a list of capability IDs that were successfully registered.
        """
        registered: List[str] = []
        seen_ids: Set[str] = set()

        for doc in self.loader.documents:
            # Look for capability metadata in the document
            cap_type = doc.metadata.get("capability_type")
            cap_id = doc.metadata.get("capability_id")

            if cap_type and cap_id:
                self.logger.info(
                    "Discovered capability metadata",
                    id=cap_id,
                    type=cap_type,
                    path=doc.path,
                )

                # Validate and build descriptor
                try:
                    descriptor = await validate_and_build_descriptor(
                        metadata=doc.metadata,
                        source_document=doc.path,
                        existing_ids=seen_ids,
                    )

                    # Register the descriptor
                    try:
                        await self.registry.register(descriptor)
                        seen_ids.add(descriptor.id)
                        self.logger.info(
                            "Capability descriptor registered",
                            id=cap_id,
                            implementation=descriptor.implementation,
                        )
                        registered.append(cap_id)
                    except Exception as e:
                        self.logger.error(
                            "Failed to register capability descriptor",
                            id=cap_id,
                            error=str(e),
                            exc_info=True,
                        )
                except ValidationError as e:
                    self.logger.error(
                        "Capability metadata validation failed",
                        capability_id=e.capability_id,
                        errors=e.errors,
                    )
                    # Continue to next document (fail fast for this capability only)
            else:
                self.logger.debug(
                    "Document lacks capability metadata",
                    path=doc.path,
                )

        return registered

    async def validate_only(self) -> List[str]:
        """Validate all capability metadata without registering.

        Returns a list of capability IDs that passed validation.
        """
        valid_ids: List[str] = []
        seen_ids: Set[str] = set()

        for doc in self.loader.documents:
            cap_type = doc.metadata.get("capability_type")
            cap_id = doc.metadata.get("capability_id")

            if cap_type and cap_id:
                self.logger.info(
                    "Validating capability metadata",
                    id=cap_id,
                    type=cap_type,
                    path=doc.path,
                )

                try:
                    await validate_and_build_descriptor(
                        metadata=doc.metadata,
                        source_document=doc.path,
                        existing_ids=seen_ids,
                    )
                    seen_ids.add(cap_id)
                    valid_ids.append(cap_id)
                    self.logger.info("Validation passed", capability_id=cap_id)
                except ValidationError as e:
                    self.logger.error(
                        "Capability metadata validation failed",
                        capability_id=e.capability_id,
                        errors=e.errors,
                    )
            else:
                self.logger.debug(
                    "Document lacks capability metadata",
                    path=doc.path,
                )

        return valid_ids