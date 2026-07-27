"""
Telemetry Models — Phase 1
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TelemetrySeverity(str, Enum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TelemetryEvent(BaseModel):
    """Event telemetry yang tercatat di runtime."""

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    event_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    runtime_state: Optional[str] = None
    component: str = "runtime"
    severity: TelemetrySeverity = TelemetrySeverity.INFO
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class MetricPoint(BaseModel):
    """Single metric point dengan labels."""

    name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)


class RuntimeMetrics(BaseModel):
    """Snapshot metrics runtime pada satu titik waktu."""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: float = 0.0
    workflow_count: int = 0
    plugin_count: int = 0
    health_score: float = 100.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
