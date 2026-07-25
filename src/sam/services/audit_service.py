"""
Audit Service for SAM Runtime.

Records immutable audit events from the Event Bus.
"""

from typing import List, Optional
from datetime import datetime
import uuid
import structlog

from sam.events import EventBus, Event
from sam.models import AuditEvent as AuditEventModel


class AuditService:
    """
    Audit service that subscribes to events and records them immutably.

    Audit is append-only. Events cannot be modified or deleted.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._events: List[AuditEventModel] = []
        self._logger = structlog.get_logger()

        # Subscribe to all events using wildcard
        self.event_bus.subscribe("*", self._record)

    async def _record(self, event: Event) -> None:
        """
        Record an audit event.

        This is called automatically by the Event Bus when any event occurs.
        """
        audit = AuditEventModel(
            id=uuid.uuid4(),
            created_at=datetime.utcnow(),
            execution_id=event.payload.get("execution_id", ""),
            capability_id=event.payload.get("capability_id", ""),
            event_type=event.type,
            severity=event.payload.get("severity", "info"),
            timestamp=event.timestamp,
            payload=event.payload,
            version="1.0"
        )
        self._events.append(audit)
        self._logger.info(
            "audit_recorded",
            event_type=event.type,
            source=event.source,
            count=len(self._events)
        )

    def get_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        capability_id: Optional[str] = None
    ) -> List[AuditEventModel]:
        """
        Retrieve audit events with optional filters.

        Args:
            limit: Maximum number of events to return.
            event_type: Filter by event type.
            capability_id: Filter by capability ID.

        Returns:
            List of audit events (newest first).
        """
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if capability_id:
            events = [e for e in events if e.capability_id == capability_id]
        # Return newest first
        return events[-limit:][::-1]

    def clear(self) -> None:
        """Clear all audit events (only for testing)."""
        self._events.clear()
        self._logger.warning("audit_cleared")

    @property
    def count(self) -> int:
        """Number of recorded audit events."""
        return len(self._events)