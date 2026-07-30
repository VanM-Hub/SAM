"""Execution Monitoring DTOs — frozen."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Dict


@dataclass(frozen=True)
class MonitorEvent:
    event_id: str
    timestamp: float
    source: str
    level: str = "info"
    message: str = ""
    metrics: Tuple[tuple, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MonitorSnapshot:
    snapshot_id: str
    timestamp: float
    total_events: int = 0
    active_candidates: int = 0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    status: str = "ok"


@dataclass(frozen=True)
class HealthStatus:
    overall: str = "healthy"
    score: float = 100.0
    issues: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MonitorMetrics:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    io_ops: int = 0
    active_threads: int = 0
    average_latency_ms: float = 0.0
