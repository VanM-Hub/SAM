from __future__ import annotations

from typing import Dict, List, Callable, Awaitable, Optional
import structlog
import asyncio
from dataclasses import dataclass, field

from .events import Event


@dataclass
class Subscription:
    event_type: str
    handler: Callable[[Event], Awaitable[None]]


class EventBus:
    """Event bus for inter-service communication."""

    def __init__(self):
        self._subscriptions: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._logger = structlog.get_logger()
        self._closed = False

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Subscribe to an event type."""
        if self._closed:
            raise RuntimeError("Event bus is closed")
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(handler)
        self._logger.debug("subscribed", event_type=event_type)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [h for h in self._subscriptions[event_type] if h != handler]
            if not self._subscriptions[event_type]:
                del self._subscriptions[event_type]
            self._logger.debug("unsubscribed", event_type=event_type)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if self._closed:
            self._logger.warning("event_published_to_closed_bus", event_type=event.type)
            return

        self._logger.debug("publishing_event", event_type=event.type, source=event.source)

        handlers = self._subscriptions.get(event.type, [])
        wildcard_handlers = self._subscriptions.get("*", [])

        for handler in handlers + wildcard_handlers:
            try:
                await handler(event)
            except Exception as e:
                self._logger.error(
                    "event_handler_failed",
                    event_type=event.type,
                    handler=getattr(handler, "__name__", str(handler)),
                    error=str(e)
                )

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscriptions.clear()
        self._logger.debug("event_bus_cleared")

    def close(self) -> None:
        """Close the event bus (no new subscriptions)."""
        self._closed = True
        self._logger.info("event_bus_closed")
