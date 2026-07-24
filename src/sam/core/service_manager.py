from __future__ import annotations

from typing import Dict, List, Optional
import structlog

from .service import RuntimeService
from .health import ServiceHealth
from .event_bus import EventBus


class ServiceManager:
    """Manages lifecycle of all runtime services."""

    def __init__(self, event_bus: EventBus):
        self._services: Dict[str, RuntimeService] = {}
        self._logger = structlog.get_logger()
        self._event_bus = event_bus

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

    async def initialize_all(self) -> None:
        """Initialize all registered services."""
        self._logger.info("initializing_all_services", count=len(self._services))
        for name, service in self._services.items():
            try:
                await service.initialize()
                service._initialized = True
                self._logger.info("service_initialized", name=name)
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
