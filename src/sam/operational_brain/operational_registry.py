"""Operational Registry — menyimpan goal, kandidat, snapshot."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate


@dataclass(frozen=True)
class OperationalSnapshot:
    """Immutable snapshot dari registry pada suatu waktu."""
    goals: int = 0
    candidates: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    avg_priority: float = 0.0
    avg_score: float = 0.0
    avg_urgency: float = 0.0
    avg_confidence: float = 0.0


class OperationalRegistry:
    """Registry menyimpan goal dan kandidat tanpa mengambil keputusan."""

    def __init__(self):
        self._goals: Dict[str, OperationalGoal] = {}
        self._candidates: Dict[str, OperationalCandidate] = {}

    def register_goal(self, goal: OperationalGoal) -> None:
        if goal.goal_id in self._goals:
            raise ValueError(f"Goal '{goal.goal_id}' already registered")
        self._goals[goal.goal_id] = goal

    def remove_goal(self, goal_id: str) -> bool:
        if goal_id in self._goals:
            del self._goals[goal_id]
            return True
        return False

    def find_goal(self, goal_id: str) -> Optional[OperationalGoal]:
        return self._goals.get(goal_id)

    def list_goals(self) -> List[OperationalGoal]:
        return list(self._goals.values())

    def register_candidate(self, candidate: OperationalCandidate) -> None:
        if candidate.candidate_id in self._candidates:
            raise ValueError(f"Candidate '{candidate.candidate_id}' already registered")
        self._candidates[candidate.candidate_id] = candidate

    def list_candidates(self) -> List[OperationalCandidate]:
        return list(self._candidates.values())

    def find_candidate(self, candidate_id: str) -> Optional[OperationalCandidate]:
        return self._candidates.get(candidate_id)

    def remove_candidate(self, candidate_id: str) -> bool:
        if candidate_id in self._candidates:
            del self._candidates[candidate_id]
            return True
        return False

    def clear(self) -> None:
        self._goals.clear()
        self._candidates.clear()

    @property
    def goal_count(self) -> int:
        return len(self._goals)

    @property
    def candidate_count(self) -> int:
        return len(self._candidates)

    def statistics(self) -> OperationalSnapshot:
        by_type: Dict[str, int] = {}
        for g in self._goals.values():
            t = g.goal_type.name
            by_type[t] = by_type.get(t, 0) + 1
        priorities = [g.priority for g in self._goals.values()]
        scores = [c.score for c in self._candidates.values()]
        urgencies = [c.urgency for c in self._candidates.values()]
        confidences = [c.confidence for c in self._candidates.values()]

        def avg(vals):
            return sum(vals) / len(vals) if vals else 0.0

        return OperationalSnapshot(
            goals=self.goal_count,
            candidates=self.candidate_count,
            by_type=by_type,
            avg_priority=avg(priorities),
            avg_score=avg(scores),
            avg_urgency=avg(urgencies),
            avg_confidence=avg(confidences),
        )

    def snapshot(self) -> OperationalSnapshot:
        """Immutable snapshot — tidak bisa diubah setelah dibuat."""
        return self.statistics()
