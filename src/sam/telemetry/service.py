import asyncio
import structlog
from typing import Optional, List, Dict, Any, Callable, AsyncGenerator
from datetime import datetime

from .event import TelemetryEvent, EventSeverity, EventCategory
from .event_type import TelemetryEventType
from .component import Component
from .ring_buffer import RingBuffer
from .filters import Filter
from .storage import TelemetryStorage

logger = structlog.get_logger()


class TelemetryService:
    """Single source of truth for all SAM observability."""

    def __init__(self, max_events: int = 1000, enable_cache: bool = True):
        self._buffer = RingBuffer(max_events)
        self._subscribers: List[Callable[[TelemetryEvent], None]] = []
        self._storage = TelemetryStorage() if enable_cache else None
        self._closed = False

    def emit(self, event: TelemetryEvent) -> None:
        """Emit an event. This is the ONLY way to output operational data."""
        if self._closed:
            logger.warning("telemetry_closed", event_type=event.type.value)
            return

        # Store in ring buffer
        self._buffer.push(event)

        # Store in cache if enabled
        if self._storage:
            self._storage.save(event)

        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error("subscriber_failed", error=str(e))

        logger.debug("event_emitted", type=event.type.value, component=event.component.value)

    def subscribe(self, callback: Callable[[TelemetryEvent], None]) -> None:
        """Subscribe to all events."""
        if self._closed:
            raise RuntimeError("Telemetry service is closed")
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[TelemetryEvent], None]) -> None:
        """Unsubscribe from events."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def query(self, filters: Optional[Dict] = None) -> List[TelemetryEvent]:
        """Query events from ring buffer with filters."""
        events = self._buffer.get_all()

        if filters:
            events = Filter.apply(events, filters)

        return events

    def get_recent(self, limit: int = 50) -> List[TelemetryEvent]:
        """Get recent events."""
        return self._buffer.get_recent(limit)

    async def follow(self) -> AsyncGenerator[TelemetryEvent, None]:
        """Stream events in real-time (for SSE)."""
        while not self._closed:
            latest = self._buffer.get_latest()
            if latest is not None:
                yield latest
            await asyncio.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        return {
            "total_events": len(self._buffer),
            "max_events": self._buffer.max_size,
            "subscribers": len(self._subscribers),
            "cache_enabled": self._storage is not None,
            "cache_size": self._storage.count() if self._storage else 0,
        }

    def close(self) -> None:
        """Close the telemetry service."""
        self._closed = True
        if self._storage:
            self._storage.close()
        logger.info("telemetry_closed")
