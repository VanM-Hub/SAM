"""
Event Bus for SAM Runtime.

Provides publish-subscribe communication between components.
"""

from typing import Dict, List, Callable, Any, Awaitable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()


@dataclass
class Event:
    """Base event structure."""

    type: str
    source: str
    payload: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """
    Simple in-memory event bus.

    Components publish events and subscribe to event types.
    Supports wildcard subscription "*" to receive all events.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._logger = structlog.get_logger()

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: The event type to subscribe to (e.g., "CapabilityStarted").
                        Use "*" to subscribe to all events.
            handler: Async function that receives an Event.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.info("subscribed", event_type=event_type, handler=handler.__name__)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Remove a handler subscription."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]
            self._logger.info("unsubscribed", event_type=event_type)

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: The Event to publish.
        """
        self._logger.info("publishing", event_type=event.type, source=event.source, id=event.id)

        # Get specific handlers for this event type
        handlers = self._subscribers.get(event.type, []).copy()
        # Also include wildcard subscribers if any
        if "*" in self._subscribers:
            handlers.extend(self._subscribers["*"])

        if not handlers:
            self._logger.debug("no_subscribers", event_type=event.type)
            return

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self._logger.error(
                    "handler_failed",
                    event_type=event.type,
                    handler=handler.__name__,
                    error=str(e)
                )

    def clear(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
        self._logger.info("event_bus_cleared")