"""Activation Snapshot — snapshot keadaan aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_metrics import ActivationMetrics
from sam.activation.activation_history import HistoryEntry


@dataclass(frozen=True)
class ActivationSnapshotState:
    snapshot_id: str = ""
    total_packages: int = 0
    total_events: int = 0
    total_history: int = 0
    status: str = "idle"
    metrics: Optional[ActivationMetrics] = None
    recent_events: List[str] = field(default_factory=list)
