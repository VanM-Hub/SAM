"""Execution Runtime Monitoring — frozen DTOs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Alert:
    """Alert eksekusi."""
    alert_id: str
    timestamp: float
    severity: str  # critical, warning, info
    message: str
    source: str = "execution_runtime"
    candidate_id: str = ""
    acknowledged: bool = False


@dataclass(frozen=True)
class AlertRule:
    """Aturan alert."""
    rule_id: str
    name: str
    metric: str
    operator: str  # gt, lt, eq, gte, lte
    threshold: float
    severity: str = "warning"


@dataclass(frozen=True)
class AlertHistory:
    """Riwayat alert."""
    alerts: Tuple[Alert, ...] = field(default_factory=tuple)
    total_alerts: int = 0
    latest_timestamp: float = 0.0


@dataclass(frozen=True)
class AlertSummary:
    """Ringkasan alert."""
    total_alerts: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    acknowledged_count: int = 0
    status: str = "clear"
