"""Activation Priority — prioritas aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PriorityAssignment:
    candidate_id: str = ""
    priority: int = 1  # 1 = tertinggi
    reason: str = ""


class ActivationPriority:
    """Menentukan prioritas kandidat aktivasi."""

    def assign(self, candidates: List[Any]) -> List[PriorityAssignment]:
        sorted_cands = sorted(candidates,
                              key=lambda c: (c.priority_score, c.confidence),
                              reverse=True)
        return [
            PriorityAssignment(c.candidate_id, i + 1,
                               f"score={c.priority_score}, conf={c.confidence}")
            for i, c in enumerate(sorted_cands)
        ]

    def top_n(self, assignments: List[PriorityAssignment], n: int = 3) -> List[PriorityAssignment]:
        return sorted(assignments, key=lambda a: a.priority)[:n]
