from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from .clock import TimeProvider, SystemClock


class HealthStatus(str, Enum):
    """Health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health status of a service."""

    status: HealthStatus
    message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None

    @classmethod
    def healthy(cls, message: Optional[str] = None,
                clock: Optional[TimeProvider] = None) -> "ServiceHealth":
        c = clock or SystemClock()
        return cls(status=HealthStatus.HEALTHY, message=message, last_check=c.now())

    @classmethod
    def degraded(cls, message: str,
                 clock: Optional[TimeProvider] = None) -> "ServiceHealth":
        c = clock or SystemClock()
        return cls(status=HealthStatus.DEGRADED, message=message, last_check=c.now())

    @classmethod
    def unhealthy(cls, message: str,
                  clock: Optional[TimeProvider] = None) -> "ServiceHealth":
        c = clock or SystemClock()
        return cls(status=HealthStatus.UNHEALTHY, message=message, last_check=c.now())

    @classmethod
    def unknown(cls, message: Optional[str] = None,
                clock: Optional[TimeProvider] = None) -> "ServiceHealth":
        c = clock or SystemClock()
        return cls(status=HealthStatus.UNKNOWN, message=message, last_check=c.now())
