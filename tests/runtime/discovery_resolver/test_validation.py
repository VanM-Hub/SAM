"""Tests for validators: RequestValidator, RegistryValidator, ResolutionValidator.

Authority: I2-003 §4
"""

import pytest

from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    CapabilityRequest,
    RegistryEntry,
    ResolverLifecycleState,
)
from sam.runtime.discovery_resolver.validation.request_validator import (
    RequestValidator,
)
from sam.runtime.discovery_resolver.validation.registry_validator import (
    RegistryValidator,
)
from sam.runtime.discovery_resolver.validation.resolution_validator import (
    ResolutionValidator,
)
from sam.runtime.discovery_resolver.exceptions.resolution_errors import (
    InvalidRequest,
    InvalidRegistryEntry,
    ResolutionNotDeterministic,
)


class TestRequestValidator:
    """Tests for RequestValidator."""

    def setup_method(self) -> None:
        self.val = RequestValidator()

    def test_valid_request(self) -> None:
        """Valid request passes."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        assert self.val.validate(req) is True

    def test_empty_identity(self) -> None:
        """Empty identity raises InvalidRequest."""
        req = CapabilityRequest("", "1.0.0", "test")
        with pytest.raises(InvalidRequest, match="identity"):
            self.val.validate(req)

    def test_empty_version(self) -> None:
        """Empty version raises InvalidRequest."""
        req = CapabilityRequest("memory.lookup", "", "test")
        with pytest.raises(InvalidRequest, match="version"):
            self.val.validate(req)

    def test_empty_requester(self) -> None:
        """Empty requester raises InvalidRequest."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "")
        with pytest.raises(InvalidRequest, match="(?i)requester"):
            self.val.validate(req)

    def test_invalid_version_format(self) -> None:
        """Non-semver version raises InvalidRequest."""
        req = CapabilityRequest("memory.lookup", "v1.0", "test")
        with pytest.raises(InvalidRequest):
            self.val.validate(req)

    def test_whitespace_identity(self) -> None:
        """Whitespace-only identity raises InvalidRequest."""
        req = CapabilityRequest("   ", "1.0.0", "test")
        with pytest.raises(InvalidRequest):
            self.val.validate(req)


class TestRegistryEntryValidator:
    """Tests for RegistryValidator."""

    def setup_method(self) -> None:
        self.val = RegistryValidator()

    def test_valid_entry(self) -> None:
        """Valid entry passes."""
        entry = RegistryEntry("memory.lookup", "Memory Lookup", "1.0.0")
        assert self.val.validate(entry) is True

    def test_empty_identity(self) -> None:
        """Empty identity raises InvalidRegistryEntry."""
        entry = RegistryEntry("", "Name", "1.0.0")
        with pytest.raises(InvalidRegistryEntry, match="identity"):
            self.val.validate(entry)

    def test_empty_name(self) -> None:
        """Empty name raises InvalidRegistryEntry."""
        entry = RegistryEntry("memory.lookup", "", "1.0.0")
        with pytest.raises(InvalidRegistryEntry, match="name"):
            self.val.validate(entry)

    def test_empty_version(self) -> None:
        """Empty version raises InvalidRegistryEntry."""
        entry = RegistryEntry("memory.lookup", "Name", "")
        with pytest.raises(InvalidRegistryEntry, match="version"):
            self.val.validate(entry)

    def test_invalid_lifecycle_state(self) -> None:
        """Unknown lifecycle state raises InvalidRegistryEntry."""
        entry = RegistryEntry(
            "memory.lookup", "Name", "1.0.0",
            lifecycle_state="UNKNOWN",
        )
        with pytest.raises(InvalidRegistryEntry, match="lifecycle"):
            self.val.validate(entry)

    def test_all_valid_lifecycle_states(self) -> None:
        """All standard lifecycle states pass."""
        for state in [
            "DECLARED", "REGISTERED", "CERTIFIED", "AVAILABLE",
            "DEPRECATED", "RETIRED", "SUSPENDED", "REMOVED",
        ]:
            entry = RegistryEntry(
                "memory.lookup", "Name", "1.0.0",
                lifecycle_state=state,
            )
            assert self.val.validate(entry) is True


class TestResolutionValidator:
    """Tests for ResolutionValidator — determinism checks."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

    def test_determinism_passes(self) -> None:
        """Same request N times → same result → passes."""
        self.resolver.register_entry(
            RegistryEntry("memory.lookup", "Test", "1.0.0")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        assert ResolutionValidator.validate_determinism(
            self.resolver, req, iterations=10,
        ) is True

    def test_side_effect_free(self) -> None:
        """Registry count unchanged after N resolutions."""
        self.resolver.register_entry(
            RegistryEntry("memory.lookup", "Test", "1.0.0")
        )
        self.resolver.register_entry(
            RegistryEntry("knowledge.search", "Test", "1.0.0")
        )
        initial = len(self.resolver.list_entries())
        for _ in range(20):
            req = CapabilityRequest("memory.lookup", "1.0.0", "test")
            self.resolver.resolve(req)
        assert ResolutionValidator.validate_side_effect_free(
            self.resolver, initial,
        ) is True
