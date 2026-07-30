"""Activation Context DTO — keadaan saat aktivasi dimulai.

Menerjemahkan Operational Plan menjadi Activation Context.
Immutable, frozen dataclass.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ActivationContext:
    """Snapshot lingkungan untuk proses aktivasi — immutable."""
    context_id: str
    timestamp: float
    source_plan: str = ""  # operational plan id sumber
    environment: str = "normal"  # normal, busy, emergency, idle
    total_candidates: int = 0
    total_goals: int = 0
    decision_id: Optional[str] = None
    approval_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp,
            "source_plan": self.source_plan,
            "environment": self.environment,
            "total_candidates": self.total_candidates,
            "total_goals": self.total_goals,
            "decision_id": self.decision_id,
            "approval_id": self.approval_id,
            "metadata": dict(self.metadata),
        }
