from collections import deque
from typing import List, Optional

from .event import TelemetryEvent


class RingBuffer:
    """Ring buffer for telemetry events (in-memory)."""

    def __init__(self, max_size: int = 1000):
        self._buffer = deque(maxlen=max_size)
        self.max_size = max_size

    def push(self, event: TelemetryEvent) -> None:
        """Add an event to the buffer."""
        self._buffer.append(event)

    def get_recent(self, limit: int = 50) -> List[TelemetryEvent]:
        """Get recent events."""
        return list(self._buffer)[-limit:]

    def get_all(self) -> List[TelemetryEvent]:
        """Get all events in the buffer."""
        return list(self._buffer)

    def get_latest(self) -> Optional[TelemetryEvent]:
        """Get the latest event."""
        return self._buffer[-1] if self._buffer else None

    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)
