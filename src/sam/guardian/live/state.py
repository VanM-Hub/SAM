"""
Guardian Live Runtime State DTOs.

Immutable data transfer objects for runtime synchronization.
All DTOs are frozen. No async, no threading, no network.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from datetime import datetime


class RuntimeStatus(Enum):
    """Runtime status indicator."""
    RUNNING = auto()
    STOPPED = auto()
    DEGRADED = auto()
    ERROR = auto()
    UNKNOWN = auto()


class RuntimeHealth(Enum):
    """Runtime health level."""
    HEALTHY = auto()
    DEGRADED = auto()
    CRITICAL = auto()
    UNKNOWN = auto()


class RuntimeVersion(Enum):
    """Known runtime version identifiers."""
    V5_0_0 = "5.0.0"
    V4_46_0 = "4.46.0"
    V4_45_0 = "4.45.0"
    V4_44_0 = "4.44.0"
    UNKNOWN = "0.0.0"

    @classmethod
    def current(cls) -> "RuntimeVersion":
        return cls.V5_0_0

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RuntimeStatistics:
    """Immutable runtime statistics snapshot."""

    total_dispatched: int = 0
    subscriber_count: int = 0
    error_count: int = 0
    history_count: int = 0
    trigger_count: int = 0
    feed_count: int = 0
    preview_count: int = 0
    timestamp: float = 0.0

    @staticmethod
    def empty() -> "RuntimeStatistics":
        return RuntimeStatistics(timestamp=datetime.now().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_dispatched": self.total_dispatched,
            "subscriber_count": self.subscriber_count,
            "error_count": self.error_count,
            "history_count": self.history_count,
            "trigger_count": self.trigger_count,
            "feed_count": self.feed_count,
            "preview_count": self.preview_count,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class RuntimeState:
    """
    Immutable snapshot of a single runtime's state.

    Captures version, health, status, and statistics
    at a point in time.
    """

    runtime_id: str
    version: RuntimeVersion = RuntimeVersion.current()
    health: RuntimeHealth = RuntimeHealth.UNKNOWN
    status: RuntimeStatus = RuntimeStatus.UNKNOWN
    statistics: RuntimeStatistics = field(default_factory=RuntimeStatistics.empty)
    last_sync_at: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "version": str(self.version),
            "health": self.health.name,
            "status": self.status.name,
            "statistics": self.statistics.to_dict(),
            "last_sync_at": self.last_sync_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeSnapshot:
    """
    Immutable aggregate snapshot of all registered runtimes.

    Captures the complete synchronization landscape.
    """

    snapshot_id: str
    timestamp: float
    total_runtimes: int
    runtimes: Dict[str, RuntimeState]
    statistics: RuntimeStatistics
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "total_runtimes": self.total_runtimes,
            "runtimes": {k: v.to_dict() for k, v in self.runtimes.items()},
            "statistics": self.statistics.to_dict(),
            "errors": list(self.errors),
        }
