"""Activation Request DTO — permintaan aktivasi yang masuk."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass(frozen=True)
class ActivationRequest:
    """Permintaan aktivasi dari upstream (Operational Plan) — immutable."""
    request_id: str
    plan_id: str
    timestamp: float = 0.0
    requester: str = "system"
    priority: str = "normal"  # low, normal, high, critical
    context_ref: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
