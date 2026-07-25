from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import structlog

import uuid
from datetime import datetime
from typing import Dict, List, Optional

import structlog

from .service import RuntimeService
from .health import ServiceHealth
from .event_bus import EventBus
from .state import StateStore, StateRecord, StateType
from .resource import RuntimeResource, ResourceType, ResourceStatus
from .resource_manager import ResourceManager


class ServiceManager:
    """Manages lifecycle of all runtime services.

    Integrates with:
    - StateStore: persist service lifecycle states
    - ResourceManager: register services as managed RuntimeResources
    """

    def __init__(
        self,
        event_bus: EventBus,
        state_store: Optional[StateStore] = None,
        resource_manager: Optional[ResourceManager] = None,
    ):
        self._services: Dict[str, RuntimeService] = {}
        self._logger = structlog.get_logger()
        self._event_bus = event_bus
        self._state_store = state_store
        self._resource_manager = resource_manager

    def register(self, service: RuntimeService) -> None:
        """Register a service and inject EventBus if supported."""
        if service.name in self._services:
            raise ValueError(f"Service already registered: {service.name}")
        # Inject event bus if service supports it
        if hasattr(service, "set_event_bus") and callable(getattr(service, "set_event_bus")):
            service.set_event_bus(self._event_bus)
        elif hasattr(service, "inject_event_bus") and callable(getattr(service, "inject_event_bus")):
            service.inject_event_bus(self._event_bus)

        self._services[service.name] = service
        self._logger.info("service_registered", name=service.name)

        # Register as a RuntimeResource
        if self._resource_manager:
            import asyncio
            try:
                asyncio.get_running_loop()
                # event loop available — we can await directly
                asyncio.ensure_future(self._register_service_resource(service))
            except RuntimeError:
                pass  # no event loop, skip resource registration for now

    async def initialize_all(self) -> None:
        """Initialize all registered services."""
        self._logger.info("initializing_all_services", count=len(self._services))
        for name, service in self._services.items():
            try:
                await service.initialize()
                service._initialized = True
                self._logger.info("service_initialized", name=name)
                await self._save_service_state(name, "initialized")
            except Exception as e:
                self._logger.error("service_initialize_failed", name=name, error=str(e))
                raise

    async def start_all(self) -> None:
        """Start all registered services."""
        self._logger.info("starting_all_services", count=len(self._services))
        for name, service in self._services.items():
            if not service.initialized:
                raise RuntimeError(f"Service not initialized: {name}")
            try:
                await service.start()
                service._started = True
                self._logger.info("service_started", name=name)
                await self._save_service_state(name, "running")
            except Exception as e:
                self._logger.error("service_start_failed", name=name, error=str(e))
                raise

    async def health_all(self) -> Dict[str, ServiceHealth]:
        """Check health of all services."""
        results = {}
        for name, service in self._services.items():
            try:
                results[name] = await service.health()
            except Exception as e:
                self._logger.error("service_health_check_failed", name=name, error=str(e))
                results[name] = ServiceHealth.unhealthy(f"Health check failed: {e}")
        return results

    async def stop_all(self) -> None:
        """Stop all services gracefully."""
        self._logger.info("stopping_all_services", count=len(self._services))
        for name, service in list(self._services.items())[::-1]:  # reverse order
            try:
                await service.stop()
                service._stopped = True
                service._started = False
                self._logger.info("service_stopped", name=name)
                await self._save_service_state(name, "stopped")
            except Exception as e:
                self._logger.error("service_stop_failed", name=name, error=str(e))

    def get_service(self, name: str) -> Optional[RuntimeService]:
        """Get service by name."""
        return self._services.get(name)

    def get_event_bus(self) -> EventBus:
        """Return the EventBus instance used by this ServiceManager."""
        return self._event_bus

    def list_services(self) -> List[str]:
        """List all registered service names."""
        return list(self._services.keys())

    # ── State store integration ──────────────────────────────────────

    def get_state_store(self) -> Optional[StateStore]:
        """Return the StateStore instance."""
        return self._state_store

    async def restore_service_states(self) -> Dict[str, str]:
        """Restore service states from StateStore.

        Returns a dict of service name -> last known status.
        """
        if not self._state_store:
            return {}
        records = await self._state_store.list(type=StateType.SERVICE)
        result: Dict[str, str] = {}
        for rec in records:
            result[rec.name] = rec.status
        return result

    # ── Resource manager integration ────────────────────────────────

    def get_resource_manager(self) -> Optional[ResourceManager]:
        """Return the ResourceManager instance."""
        return self._resource_manager

    async def _register_service_resource(self, service: RuntimeService) -> None:
        """Register a service as a RuntimeResource with ResourceManager."""
        if not self._resource_manager:
            return
        # Check if already registered
        existing = await self._resource_manager.list(type=ResourceType.SERVICE)
        for res in existing:
            if res.name == service.name:
                self._logger.debug("service_resource_exists", name=service.name, id=res.id)
                return

        resource = RuntimeResource(
            id=str(uuid.uuid4()),
            type=ResourceType.SERVICE,
            name=service.name,
            status=ResourceStatus.CREATED,
            data={
                "initialized": service.initialized,
                "started": service.started,
            },
        )
        await self._resource_manager.register(resource)
        self._logger.info("service_resource_registered", name=service.name, id=resource.id)

    async def update_service_resource_status(self, name: str, status: ResourceStatus) -> None:
        """Update the ResourceManager status for a given service."""
        if not self._resource_manager:
            return
        existing = await self._resource_manager.list(type=ResourceType.SERVICE)
        for res in existing:
            if res.name == name:
                await self._resource_manager.update_status(res.id, status)
                break

    async def _save_service_state(self, name: str, status: str) -> None:
        """Persist service state to the StateStore and update resource status."""
        # Update ResourceManager status
        if status == "running":
            await self.update_service_resource_status(name, ResourceStatus.ACTIVE)
        elif status == "stopped":
            await self.update_service_resource_status(name, ResourceStatus.RETIRED)
        elif status == "initialized":
            await self.update_service_resource_status(name, ResourceStatus.LOADED)

        if not self._state_store:
            return
        service = self._services.get(name)

        # Check if a state record already exists for this service name+type
        existing = await self._state_store.get_by_type_and_name("SERVICE", name)

        if existing:
            # Update existing record with new status + incremented version
            existing.status = status
            existing.data = {
                "initialized": service.initialized if service else False,
                "started": service.started if service else False,
                "stopped": service.stopped if service else False,
            }
            existing.updated_at = datetime.now()
            await self._state_store.save(existing)
        else:
            record = StateRecord(
                id=str(uuid.uuid4()),
                type=StateType.SERVICE,
                name=name,
                status=status,
                data={
                    "initialized": service.initialized if service else False,
                    "started": service.started if service else False,
                    "stopped": service.stopped if service else False,
                },
                updated_at=datetime.now(),
                version=1,
            )
            await self._state_store.save(record)
