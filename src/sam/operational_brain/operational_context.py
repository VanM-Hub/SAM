"""Operational Context DTO — snapshot keadaan operasional SAM."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class OperationalContext:
    """Immutable snapshot of current operational state.

    Menangkap apa yang sedang terjadi di SAM pada suatu titik waktu.
    BUKAN Decision Runtime — hanya membaca, tidak memutuskan.
    """
    context_id: str
    timestamp: float
    source: str                         # "manual", "inbox", "timer", "event"
    environment: str                    # "normal", "busy", "idle", "emergency"
    active_missions: List[str] = field(default_factory=list)
    pending_decisions: int = 0
    pending_approvals: int = 0
    available_resources: int = 0
    active_constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "environment": self.environment,
            "active_missions": list(self.active_missions),
            "pending_decisions": self.pending_decisions,
            "pending_approvals": self.pending_approvals,
            "available_resources": self.available_resources,
            "active_constraints": list(self.active_constraints),
            "metadata": dict(self.metadata),
        }
