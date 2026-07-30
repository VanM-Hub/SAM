"""Activation Sequence — urutan aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Forward declarations for type hints
ActivationStrategy = Any
PriorityAssignment = Any


@dataclass(frozen=True)
class ActivationStep:
    step_id: str = ""
    order: int = 0
    candidate_ref: str = ""
    action: str = "activate"
    status: str = "pending"


@dataclass(frozen=True)
class ActivationSequence:
    sequence_id: str = ""
    steps: List[ActivationStep] = field(default_factory=list)
    total_steps: int = 0
    strategy_ref: str = ""
    duration_estimate: float = 0.0


class SequenceBuilder:
    """Membangun urutan aktivasi."""

    def build(self, strategy: ActivationStrategy,
              assignments: List[PriorityAssignment],
              candidates: List[Any]) -> ActivationSequence:
        cand_map = {c.candidate_id: c for c in candidates}
        sorted_assign = sorted(assignments, key=lambda a: a.priority)

        steps: List[ActivationStep] = []
        for i, a in enumerate(sorted_assign):
            c = cand_map.get(a.candidate_id)
            dur = c.estimated_duration if c else 10.0
            steps.append(ActivationStep(
                step_id=f"step_{i + 1}",
                order=i + 1,
                candidate_ref=a.candidate_id,
                action="activate",
                status="pending",
            ))

        return ActivationSequence(
            sequence_id=f"seq_{len(steps)}",
            steps=steps,
            total_steps=len(steps),
            strategy_ref=strategy.strategy_id if strategy else "",
            duration_estimate=sum(
                (cand_map.get(s.candidate_ref) or Any).estimated_duration or 10.0
                for s in steps
            ),
        )
