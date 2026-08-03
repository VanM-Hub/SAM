"""Tests for PublicationService.

Verifies: declaration → descriptor flow, duplicate prevention.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import (
    CapabilityDeclaration,
    CapabilityDescriptor,
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.services.publication_service import (
    PublicationService,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidDeclaration,
    InvalidDescriptor,
)


class TestPublicationService:
    """Tests for PublicationService."""

    def setup_method(self) -> None:
        self.service = PublicationService()

    def _valid_declaration(self, identity: str = "memory.lookup") -> CapabilityDeclaration:
        return CapabilityDeclaration(
            identity=identity,
            name="Memory Lookup",
            version="1.0.0",
            description="Look up items in memory",
            owner_citizen="citizen-001",
        )

    def test_publish_valid_declaration(self) -> None:
        """A valid declaration publishes successfully."""
        decl = self._valid_declaration()
        result = self.service.publish(decl)
        assert result.success is True
        assert result.descriptor.identity == "memory.lookup"
        assert result.descriptor.lifecycle_state == CapabilityLifecycle.DECLARED

    def test_publish_creates_frozen_descriptor(self) -> None:
        """Published descriptor is a frozen CapabilityDescriptor."""
        decl = self._valid_declaration()
        result = self.service.publish(decl)
        descriptor = result.descriptor
        assert isinstance(descriptor, CapabilityDescriptor)
        with pytest.raises(Exception):
            descriptor.identity = "changed"  # type: ignore[misc]

    def test_publish_transfers_all_fields(self) -> None:
        """All declaration fields are transferred to descriptor."""
        decl = self._valid_declaration()
        result = self.service.publish(decl)
        d = result.descriptor
        assert d.identity == decl.identity
        assert d.name == decl.name
        assert d.version == decl.version
        assert d.description == decl.description
        assert d.owner_citizen == decl.owner_citizen

    def test_publish_with_implementation_name_fails(self) -> None:
        """Declaration with implementation name is rejected."""
        decl = CapabilityDeclaration(
            identity="openai.chat",
            name="Chat",
            version="1.0.0",
        )
        with pytest.raises(InvalidDeclaration):
            self.service.publish(decl)

    def test_publish_duplicate_identity_fails(self) -> None:
        """Duplicate capability identity is rejected."""
        decl1 = self._valid_declaration("memory.lookup")
        self.service.publish(decl1)
        decl2 = self._valid_declaration("memory.lookup")
        with pytest.raises(InvalidDeclaration, match="already exists"):
            self.service.publish(decl2)

    def test_get_returns_published_capability(self) -> None:
        """get() returns the published capability."""
        decl = self._valid_declaration()
        self.service.publish(decl)
        descriptor = self.service.get("memory.lookup")
        assert descriptor.identity == "memory.lookup"

    def test_get_missing_raises_key_error(self) -> None:
        """get() raises KeyError for unknown identity."""
        with pytest.raises(KeyError):
            self.service.get("nonexistent")

    def test_get_optional_returns_none_for_missing(self) -> None:
        """get_optional() returns None for unknown identity."""
        assert self.service.get_optional("nonexistent") is None

    def test_list_all_returns_all_published(self) -> None:
        """list_all() returns all published capabilities."""
        self.service.publish(self._valid_declaration("memory.lookup"))
        self.service.publish(self._valid_declaration("knowledge.search"))
        all_caps = self.service.list_all()
        assert len(all_caps) == 2
        identities = {c.identity for c in all_caps}
        assert "memory.lookup" in identities
        assert "knowledge.search" in identities

    def test_empty_version_fails(self) -> None:
        """Empty version is rejected."""
        decl = CapabilityDeclaration(
            identity="memory.lookup",
            name="Memory Lookup",
            version="",
        )
        with pytest.raises(InvalidDeclaration):
            self.service.publish(decl)
