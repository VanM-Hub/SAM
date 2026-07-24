from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import asyncio
from typing import Optional


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

    async def tick(self, seconds: float) -> None:
        """Advance time by the specified number of seconds (default: real sleep; override for virtual time)."""
        await self.sleep(seconds)


class SystemClock(TimeProvider):
    """Real system clock implementation."""

    def now(self) -> datetime:
        return datetime.utcnow()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class FrozenClock(TimeProvider):
    """Clock frozen at a specific point in time (for testing)."""

    def __init__(self, fixed_time: Optional[datetime] = None):
        self._fixed = fixed_time or datetime(2026, 1, 1, 0, 0, 0)

    def now(self) -> datetime:
        return self._fixed

    async def sleep(self, seconds: float) -> None:
        # Frozen clock does not actually sleep; time remains fixed
        pass

    def set_time(self, new_time: datetime) -> None:
        """Manually set the frozen time."""
        self._fixed = new_time


class VirtualClock(TimeProvider):
    """Virtual clock that can be advanced manually (for testing)."""

    def __init__(self, start_time: Optional[datetime] = None):
        self._now = start_time or datetime(2026, 1, 1, 0, 0, 0)
        self._advance = timedelta()

    def now(self) -> datetime:
        return self._now + self._advance

    async def sleep(self, seconds: float) -> None:
        # Virtual clock advances immediately without real delay
        self._advance += timedelta(seconds=seconds)

    async def tick(self, seconds: float) -> None:
        """Advance virtual time by the given number of seconds (no real delay)."""
        self._advance += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        """Manually advance time by the given number of seconds."""
        self._advance += timedelta(seconds=seconds)

    def reset(self) -> None:
        """Reset virtual clock to the starting time."""
        self._advance = timedelta()
