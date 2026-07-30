"""Runtime Telemetry — DTOs telemetri."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TelemetryMetric:
    metric_id: str
    name: str
    value: float = 0.0
    unit: str = ""
    subsystem: str = "kernel"


@dataclass(frozen=True)
class TelemetrySample:
    sample_id: str
    metrics: List[TelemetryMetric] = field(default_factory=list)
    timestamp: float = 0.0


@dataclass(frozen=True)
class MetricSummary:
    summary_id: str
    metric_name: str
    avg: float = 0.0
    min: float = 0.0
    max: float = 0.0
    count: int = 0


@dataclass(frozen=True)
class TelemetryReport:
    report_id: str
    timestamp: float
    samples: List[TelemetrySample] = field(default_factory=list)
    total_metrics: int = 0
