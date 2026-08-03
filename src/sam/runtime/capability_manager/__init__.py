"""
capability_manager — Capability Manager Unit (Reference Runtime Unit 2)

Manages capability publication and lifecycle: Declared → Retired.
Publishes capabilities into Registry. Owns descriptor integrity.

Authority: CAPABILITY_SPEC | R5-001 §2.2 | I0-001 §2.2 | I1-001 §2.2
"""

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.models.declaration import (
    CapabilityDeclaration,
)
from sam.runtime.capability_manager.interfaces.manager_interface import (
    CapabilityManagerInterface,
    PublishResult,
    TransitionResult,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    CapabilityError,
    InvalidDeclaration,
    InvalidTransition,
    InvalidDescriptor,
    CapabilityNotFound,
    CertificationFailed,
    DescriptorImmutable,
)

__all__ = [
    # Models
    "CapabilityDescriptor",
    "CapabilityLifecycle",
    "CapabilityDeclaration",
    # Interface
    "CapabilityManagerInterface",
    "PublishResult",
    "TransitionResult",
    # Exceptions
    "CapabilityError",
    "InvalidDeclaration",
    "InvalidTransition",
    "InvalidDescriptor",
    "CapabilityNotFound",
    "CertificationFailed",
    "DescriptorImmutable",
]
