"""Certification validation.

Validates capability certification criteria:
descriptor integrity, immutability, discoverability, governance compliance.

Deterministic: same input always yields same result.

Authority: CAPABILITY_SPEC | GOVERNANCE
"""

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    CertificationFailed,
)


class CertificationValidator:
    """Evaluates certification criteria for a capability.

    Certification verifies:
        1. Descriptor integrity (non-empty required fields).
        2. Identity format (no implementation names).
        3. Lifecycle state is REGISTERED or later.
        4. Descriptor is immutable (not in DECLARED state).

    Deterministic: same descriptor always yields the same result.

    Authority: CAPABILITY_SPEC | GOVERNANCE
    """

    def evaluate(self, descriptor: CapabilityDescriptor) -> bool:
        """Evaluate whether a capability meets certification criteria.

        Args:
            descriptor: The CapabilityDescriptor to evaluate.

        Returns:
            True if certification passes.

        Raises:
            CertificationFailed: If certification criteria are not met.
        """
        reasons = []

        # Check 1: Descriptor must have required fields
        if not descriptor.validate_identity():
            reasons.append("Invalid capability identity.")

        # Check 2: Descriptor must be immutable (not DECLARED)
        if not descriptor.is_immutable():
            reasons.append(
                "Descriptor is still in DECLARED state. "
                "Must be at least REGISTERED before certification."
            )

        # Check 3: Lifecycle must be REGISTERED or later
        if descriptor.lifecycle_state in (
            CapabilityLifecycle.DECLARED,
        ):
            reasons.append(
                "Capability must be REGISTERED before certification."
            )

        if reasons:
            raise CertificationFailed(
                identity=descriptor.identity,
                reason="; ".join(reasons),
            )

        return True
