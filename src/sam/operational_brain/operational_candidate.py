"""Operational Candidate — satu kandidat pekerjaan dari Builder."""

from dataclasses import dataclass, field
from typing import Any, Dict

from sam.operational_brain.operational_goal import OperationalGoal


@dataclass(frozen=True)
class OperationalCandidate:
    """Sebuah kandidat — apa yang bisa dikerjakan, tanpa dipilih."""
    candidate_id: str
    goal: OperationalGoal
    score: float                    # Builder assessment 0.0–1.0
    urgency: float                  # 0.0–1.0
    impact: float                   # 0.0–1.0
    effort: float                   # estimated effort 0.0–1.0 (small→big)
    confidence: float               # 0.0–1.0
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
