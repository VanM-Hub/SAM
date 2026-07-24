"""Runtime responsible for executing capabilities."""

import anyio
import inspect
from typing import Any, Dict, Optional

import structlog

from .context import ExecutionContext
from .registry import CapabilityRegistry
from .factory import CapabilityFactory
from sam.models import CapabilityDescriptor


logger = structlog.get_logger(__name__)


class CapabilityRuntime:
    """Executes capabilities using descriptors from the registry and factory.

    The runtime uses a CapabilityRegistry to look up capability descriptors
    and a CapabilityFactory to lazily instantiate capability implementations.
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        factory: Optional[CapabilityFactory] = None,
    ) -> None:
        self.registry = registry or CapabilityRegistry()
        self.factory = factory or CapabilityFactory()
        self.logger = logger.bind(component="CapabilityRuntime")

    async def execute_capability(
        self,
        capability_id: str,
        context: ExecutionContext,
        *,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute a capability with the given context.

        Args:
            capability_id: Identifier of the capability to run.
            context: ExecutionContext providing inputs and logging.
            timeout: Optional timeout in seconds; if exceeded, raises TimeoutError.

        Returns:
            The result returned by the capability's execute method.

        Raises:
            ValueError: If the capability is not found in the registry.
            TimeoutError: If the execution exceeds the timeout.
        """
        # Get descriptor from registry
        self.logger.debug("Looking up capability descriptor", capability_id=capability_id)
        descriptor = await self.registry.get_descriptor(capability_id)
        if descriptor is None:
            self.logger.error(
                "Capability not found in registry",
                capability_id=capability_id,
            )
            raise ValueError(f"Capability {capability_id} not found")

        self.logger.debug(
            "Found descriptor, creating capability instance",
            capability_id=capability_id,
            implementation=descriptor.implementation,
        )

        # Use factory to create capability instance
        capability = await self.factory.create(descriptor)

        self.logger.info(
            "Starting capability execution",
            capability_id=capability_id,
            execution_id=str(context.execution_id),
            invocation_id=str(context.invocation_id),
        )
        try:
            # Use anyio.fail_after which raises TimeoutError on timeout
            with anyio.fail_after(timeout or float("inf")):
                if inspect.iscoroutinefunction(capability.execute):
                    result = await capability.execute(context)
                else:
                    result = await anyio.run_sync_in_worker_thread(
                        capability.execute, context
                    )
        except Exception as exc:  # pragma: no cover - passthrough
            self.logger.exception(
                "Capability execution raised",
                capability_id=capability_id,
                error=str(exc),
            )
            raise
        else:
            self.logger.info(
                "Capability execution completed",
                capability_id=capability_id,
                execution_id=str(context.execution_id),
                result_type=type(result).__name__,
            )
            return result