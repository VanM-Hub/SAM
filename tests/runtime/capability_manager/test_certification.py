"""Tests for CertificationValidator.

Verifies: certification criteria, determinism, error cases.

Authority: I2-002 §6.1
"""

import pytest

from sam.runtime.capability_manager import (
    CapabilityDescriptor,
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.validation.certification_validator import (
    CertificationValidator,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    CertificationFailed,
)


class TestCertificationValidator:
    """Tests for CertificationValidator."""

    def setup_method(self) -> None:
        self.validator = CertificationValidator()

    def _make_descriptor(
        self,
        identity: str = "memory.lookup",
        state: CapabilityLifecycle = CapabilityLifecycle.REGISTERED,
    ) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            identity=identity,
            name="Memory Lookup",
            version="1.0.0",
            lifecycle_state=state,
        )

    def test_registered_capability_passes(self) -> None:
        """A REGISTERED capability passes certification."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.REGISTERED)
        assert self.validator.evaluate(descriptor) is True

    def test_certified_capability_passes(self) -> None:
        """A CERTIFIED capability passes certification."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.CERTIFIED)
        assert self.validator.evaluate(descriptor) is True

    def test_available_capability_passes(self) -> None:
        """An AVAILABLE capability passes certification."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.AVAILABLE)
        assert self.validator.evaluate(descriptor) is True

    def test_declared_state_fails(self) -> None:
        """DECLARED state is not eligible for certification."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.DECLARED)
        with pytest.raises(CertificationFailed):
            self.validator.evaluate(descriptor)

    def test_empty_identity_fails(self) -> None:
        """Empty identity fails certification."""
        descriptor = self._make_descriptor(
            identity="", state=CapabilityLifecycle.REGISTERED
        )
        with pytest.raises(CertificationFailed):
            self.validator.evaluate(descriptor)

    def test_determinism_same_input_same_result(self) -> None:
        """Same descriptor always yields same certification result."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.REGISTERED)
        results = [self.validator.evaluate(descriptor) for _ in range(5)]
        assert all(r is True for r in results)

    def test_determinism_same_input_same_failure(self) -> None:
        """Same failing descriptor always fails the same way."""
        descriptor = self._make_descriptor(state=CapabilityLifecycle.DECLARED)
        for _ in range(5):
            with pytest.raises(CertificationFailed):
                self.validator.evaluate(descriptor)
