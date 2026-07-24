from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import asyncio


class TimeProvider(ABC):
    """Abstract clock for time-related operations."""

    @abstractmethod
    def now(self) -> datetime:
        """Return current time."""
        pass

    @abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Sleep for the specified duration."""
        pass


class SystemClock(TimeProvider):
    """Real system clock implementation."""

    def now(self) -> datetime:
        return datetime.utcnow()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
