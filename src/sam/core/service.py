from __future__ import annotations

from abc import ABC, abstractmethod
import structlog

from .health import ServiceHealth


class RuntimeService(ABC):
    """Base class for all runtime services."""

    def __init__(self):
        self._logger = structlog.get_logger()
        self._initialized = False
        self._started = False
        self._stopped = False
        # Event bus will be injected by ServiceManager when available
        self._event_bus = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name (unique identifier)."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources (connections, config, etc.)."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the service (begin background operations)."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the service gracefully."""
        pass

    @abstractmethod
    async def health(self) -> ServiceHealth:
        """Return current service health status."""
        pass

    def inject_event_bus(self, event_bus) -> None:
        """Optional hook to receive EventBus instance from ServiceManager."""
        self._event_bus = event_bus

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def started(self) -> bool:
        return self._started

    @property
    def stopped(self) -> bool:
        return self._stopped
