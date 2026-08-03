"""Capability Manager main service orchestrator.

Concrete implementation of CapabilityManagerInterface.
Coordinates publication, lifecycle, health, and certification services.

Authority: R5-001 §2.2 | I0-001 §2.2
"""

from typing import List, Optional

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
from sam.runtime.capability_manager.services.publication_service import (
    PublicationService,
)
from sam.runtime.capability_manager.services.lifecycle_service import (
    LifecycleService,
)
from sam.runtime.capability_manager.services.health_service import (
    HealthService,
)
from sam.runtime.capability_manager.validation.certification_validator import (
    CertificationValidator,
)
from sam.runtime.capability_manager.lifecycle.manager_lifecycle import (
    ManagerLifecycle,
    ManagerLifecycleState,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    CapabilityNotFound,
)


class CapabilityManagerService(CapabilityManagerInterface):
    """Concrete implementation of CapabilityManagerInterface.

    Orchestrates:
        - Publication (Declaration → Descriptor)
        - Lifecycle transitions (DECLARED → ... → RETIRED)
        - Certification evaluation
        - Health reporting
        - Capability query (get, list, discoverable)

    Must not:
        - Execute capabilities
        - Resolve/discover capabilities
        - Define contracts
        - Make approval decisions
    """

    def __init__(
        self,
        publication_service: PublicationService = None,
        lifecycle_service: LifecycleService = None,
        health_service: HealthService = None,
        certification_validator: CertificationValidator = None,
        lifecycle: ManagerLifecycle = None,
    ) -> None:
        self._publication_service = (
            publication_service or PublicationService()
        )
        self._lifecycle_service = lifecycle_service or LifecycleService()
        self._health_service = health_service or HealthService()
        self._certification_validator = (
            certification_validator or CertificationValidator()
        )
        self._manager_lifecycle = lifecycle or ManagerLifecycle()

        # Start manager lifecycle
        self._manager_lifecycle.transition_to(
            ManagerLifecycleState.INITIALIZING
        )
        self._manager_lifecycle.transition_to(ManagerLifecycleState.RUNNING)
        # Sync health service lifecycle
        self._health_service = HealthService(
            lifecycle=self._manager_lifecycle
        )

    # ── CapabilityManagerInterface implementation ──────────────────

    def publish(self, declaration: CapabilityDeclaration) -> PublishResult:
        """Validate and publish a new Capability.

        Steps:
            1. Validate declaration.
            2. Create immutable descriptor.
            3. Register lifecycle.
            4. Store.

        Args:
            declaration: CapabilityDeclaration to publish.

        Returns:
            PublishResult with the published descriptor.
        """
        self._ensure_operational()

        result = self._publication_service.publish(declaration)

        # Register capability lifecycle in lifecycle service
        self._lifecycle_service.register(
            identity=result.descriptor.identity,
            state=result.descriptor.lifecycle_state,
        )

        return result

    def transition(
        self,
        identity: str,
        target_state: CapabilityLifecycle,
    ) -> TransitionResult:
        """Transition a capability to a new lifecycle state.

        Args:
            identity: The capability identity.
            target_state: Desired target lifecycle state.

        Returns:
            TransitionResult with from/to states.
        """
        self._ensure_operational()
        return self._lifecycle_service.transition(identity, target_state)

    def get_capability(
        self,
        identity: str,
    ) -> Optional[CapabilityDescriptor]:
        """Retrieve a capability descriptor by identity.

        Args:
            identity: The capability identity.

        Returns:
            CapabilityDescriptor if found, None otherwise.
        """
        return self._publication_service.get_optional(identity)

    def list_capabilities(
        self,
        lifecycle_state: Optional[CapabilityLifecycle] = None,
    ) -> List[CapabilityDescriptor]:
        """List capability descriptors, optionally filtered.

        Args:
            lifecycle_state: Optional state filter.

        Returns:
            List of matching descriptors.
        """
        all_caps = self._publication_service.list_all()
        if lifecycle_state is None:
            return all_caps
        return [c for c in all_caps if c.lifecycle_state == lifecycle_state]

    def is_discoverable(self, identity: str) -> bool:
        """Check if a capability is currently discoverable.

        Retired capabilities are not discoverable.

        Args:
            identity: The capability identity.

        Returns:
            True if the capability is not RETIRED.
        """
        descriptor = self.get_capability(identity)
        if descriptor is None:
            return False
        return descriptor.is_discoverable()

    def get_health(self) -> str:
        """Report the health status of the Capability Manager.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        return self._health_service.get_health()

    # ── Private ────────────────────────────────────────────────────

    def _ensure_operational(self) -> None:
        """Ensure the manager is in an operational state.

        Raises:
            RuntimeError: If the manager is not operational.
        """
        if not self._manager_lifecycle.is_operational():
            raise RuntimeError(
                f"Capability Manager is not operational. "
                f"Current state: {self._manager_lifecycle.state.name}"
            )
