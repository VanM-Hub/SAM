"""Runtime Health — DTOs kesehatan runtime."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class HealthCheck:
    check_id: str
    subsystem: str
    status: str = "unknown"
    latency_ms: float = 0.0
    message: str = ""


@dataclass(frozen=True)
class HealthReport:
    report_id: str
    timestamp: float
    overall: str = "unknown"
    checks: List[HealthCheck] = field(default_factory=list)


@dataclass(frozen=True)
class ResourceUsage:
    usage_id: str
    cpu_pct: float = 0.0
    memory_pct: float = 0.0
    subsystem: str = "kernel"


@dataclass(frozen=True)
class HealthThreshold:
    threshold_id: str
    metric: str
    warning: float = 80.0
    critical: float = 95.0


@dataclass(frozen=True)
class AlertRecord:
    alert_id: str
    metric: str
    value: float
    level: str = "info"
