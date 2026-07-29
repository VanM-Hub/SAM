"""
Guardian Event Publisher.

Publishes events to the dispatcher without knowing who subscribes.
Synchronous only. No async, no threading, no network.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventMetadata,
)

if TYPE_CHECKING:
    from .dispatcher import GuardianEventDispatcher


class GuardianEventPublisher:
    """
    Publishes events to the Guardian Event Dispatcher.

    The publisher has no knowledge of subscribers. It only knows
    the dispatcher it publishes to.
    """

    def __init__(self, dispatcher: "GuardianEventDispatcher") -> None:
        self._dispatcher = dispatcher

    def publish(
        self,
        event_type: GuardianEventType,
        source: GuardianEventSource,
        payload: object,
        priority: Optional[GuardianEventPriority] = None,
        correlation_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
    ) -> GuardianEvent:
        """
        Create and publish an event to the dispatcher.

        Args:
            event_type: Type of event.
            source: Source component.
            payload: Event payload data.
            priority: Priority level (default: MEDIUM).
            correlation_id: Optional correlation ID for event tracing.
            parent_event_id: Optional parent event ID for chaining.

        Returns:
            The published GuardianEvent.

        Raises:
            ValueError: If dispatcher is not set.
        """
        if self._dispatcher is None:
            raise ValueError("Dispatcher not set. Cannot publish.")

        effective_priority = priority or GuardianEventPriority.MEDIUM
        metadata = GuardianEventMetadata(
            event_type=event_type,
            priority=effective_priority,
            source=source,
            timestamp=datetime.now().timestamp(),
            version="1.0",
        )

        event = GuardianEvent(
            metadata=metadata,
            payload=payload,
            correlation_id=correlation_id,
            parent_event_id=parent_event_id,
        )

        self._dispatcher.dispatch(event)
        return event
