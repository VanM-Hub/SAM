"""Tests for CapabilityDescriptor model.

Verifies: creation, immutability, field validation, discoverability.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import (
    CapabilityDescriptor,
    CapabilityLifecycle,
)


class TestCapabilityDescriptor:
    """Tests for CapabilityDescriptor — immutable representation."""

    def test_create_descriptor_with_required_fields(self) -> None:
        """Descriptor can be created with identity, name, version."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert descriptor.identity == "memory.lookup"
        assert descriptor.name == "Memory Lookup"
        assert descriptor.version == "1.0.0"

    def test_create_descriptor_with_all_fields(self) -> None:
        """Descriptor accepts all optional fields."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
            description="Look up items in memory",
            owner_citizen="citizen-001",
            inputs=["query"],
            outputs=["results"],
            constraints=["max_results=100"],
            compatibility=["1.0.x"],
            lifecycle_state=CapabilityLifecycle.REGISTERED,
            certification_status="certified",
        )
        assert descriptor.description == "Look up items in memory"
        assert descriptor.owner_citizen == "citizen-001"
        assert descriptor.inputs == ["query"]
        assert descriptor.outputs == ["results"]
        assert descriptor.lifecycle_state == CapabilityLifecycle.REGISTERED

    def test_default_lifecycle_is_declared(self) -> None:
        """Default lifecycle state is DECLARED."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert descriptor.lifecycle_state == CapabilityLifecycle.DECLARED

    def test_descriptor_is_frozen(self) -> None:
        """CapabilityDescriptor is frozen (immutable dataclass)."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        with pytest.raises(Exception):
            descriptor.identity = "changed"  # type: ignore[misc]

    def test_validate_identity_with_value(self) -> None:
        """Validate identity returns True for non-empty identity."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert descriptor.validate_identity() is True

    def test_validate_identity_with_empty(self) -> None:
        """Validate identity returns False for empty identity."""
        descriptor = CapabilityDescriptor(
            identity="",
            name="Memory Lookup",
            version="1.0.0",
        )
        assert descriptor.validate_identity() is False

    def test_is_discoverable_when_not_retired(self) -> None:
        """Non-RETIRED capabilities are discoverable."""
        for state in CapabilityLifecycle:
            if state == CapabilityLifecycle.RETIRED:
                continue
            descriptor = CapabilityDescriptor(
                identity=f"test.{state.name.lower()}",
                name="Test",
                version="1.0.0",
                lifecycle_state=state,
            )
            assert descriptor.is_discoverable() is True

    def test_is_not_discoverable_when_retired(self) -> None:
        """RETIRED capabilities are NOT discoverable."""
        descriptor = CapabilityDescriptor(
            identity="memory.legacy",
            name="Legacy Memory",
            version="1.0.0",
            lifecycle_state=CapabilityLifecycle.RETIRED,
        )
        assert descriptor.is_discoverable() is False

    def test_is_immutable_when_not_declared(self) -> None:
        """Descriptors beyond DECLARED state are immutable."""
        for state in CapabilityLifecycle:
            if state == CapabilityLifecycle.DECLARED:
                continue
            descriptor = CapabilityDescriptor(
                identity=f"test.{state.name.lower()}",
                name="Test",
                version="1.0.0",
                lifecycle_state=state,
            )
            assert descriptor.is_immutable() is True

    def test_is_not_immutable_when_declared(self) -> None:
        """Descriptors in DECLARED state are still mutable."""
        descriptor = CapabilityDescriptor(
            identity="memory.draft",
            name="Draft",
            version="1.0.0",
            lifecycle_state=CapabilityLifecycle.DECLARED,
        )
        assert descriptor.is_immutable() is False

    def test_repr_includes_identity_and_version(self) -> None:
        """String representation includes key fields."""
        descriptor = CapabilityDescriptor(
            identity="memory.lookup",
            name="Memory Lookup",
            version="2.0.0",
        )
        r = repr(descriptor)
        assert "memory.lookup" in r
        assert "2.0.0" in r
