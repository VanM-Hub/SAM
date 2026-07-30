"""Execution Strategy — 5 tipe strategi eksekusi."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.execution.runtime.execution_candidate import ExecutionCandidate


@dataclass(frozen=True)
class StrategyResult:
    """Hasil strategi."""
    strategy_type: str
    candidate_ids: List[str]
    description: str = ""
    score: float = 0.0


class ExecutionStrategy:
    """Strategy engine — 5 tipe strategi eksekusi.

    1. sequential — eksekusi berurutan
    2. parallel — eksekusi paralel (dalam plan, bukan threading)
    3. prioritized — berdasarkan prioritas
    4. conditional — berdasarkan kondisi
    5. fallback — dengan fallback plan
    """

    def sequential(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Urutkan kandidat sequential — berdasarkan dependensi."""
        ordered = sorted(candidates, key=lambda c: len(c.dependencies))
        return StrategyResult(
            strategy_type="sequential",
            candidate_ids=[c.candidate_id for c in ordered],
            description="Sequential execution by dependency count",
            score=0.8,
        )

    def parallel(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Kandidat tanpa dependensi bisa parallel."""
        independent = [c for c in candidates if not c.dependencies]
        dependent = [c for c in candidates if c.dependencies]
        return StrategyResult(
            strategy_type="parallel",
            candidate_ids=[c.candidate_id for c in candidates],
            description=f"{len(independent)} independent, {len(dependent)} dependent",
            score=0.7,
        )

    def prioritized(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Urutkan berdasarkan effort (ascending)."""
        ordered = sorted(candidates, key=lambda c: c.estimated_effort)
        return StrategyResult(
            strategy_type="prioritized",
            candidate_ids=[c.candidate_id for c in ordered],
            description="Prioritized by estimated effort",
            score=0.9 if candidates else 0.0,
        )

    def conditional(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Berdasarkan conditional type."""
        cond = [c for c in candidates if c.candidate_type == "conditional"]
        other = [c for c in candidates if c.candidate_type != "conditional"]
        return StrategyResult(
            strategy_type="conditional",
            candidate_ids=[c.candidate_id for c in cond + other],
            description=f"{len(cond)} conditional, {len(other)} other",
            score=0.6,
        )

    def fallback(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Fallback — semua kandidat dengan prioritas default."""
        return StrategyResult(
            strategy_type="fallback",
            candidate_ids=[c.candidate_id for c in candidates],
            description="Fallback execution plan",
            score=0.5,
        )

    def auto_select(self, candidates: List[ExecutionCandidate]) -> StrategyResult:
        """Auto-select strategi berdasarkan tipe kandidat."""
        types = {c.candidate_type for c in candidates}
        if "immediate" in types:
            return self.prioritized(candidates)
        elif "scheduled" in types:
            return self.sequential(candidates)
        elif len(candidates) <= 3:
            return self.parallel(candidates)
        else:
            return self.sequential(candidates)


@dataclass(frozen=True)
class SequenceStep:
    """Satu langkah dalam sequence."""
    step_id: int
    candidate_id: str
    action: str = "execute"
    depends_on: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionSequence:
    """Sequence eksekusi — urutan langkah-langkah."""
    sequence_id: str
    steps: List[SequenceStep]
    total_steps: int
    strategy_type: str = "sequential"
    description: str = ""


class SequenceBuilder:
    """Builder untuk ExecutionSequence."""

    def build(self, strategy: StrategyResult,
              candidates: List[ExecutionCandidate]) -> ExecutionSequence:
        """Build sequence dari strategy result."""
        steps = []
        for i, cid in enumerate(strategy.candidate_ids):
            c = next((c for c in candidates if c.candidate_id == cid), None)
            deps = []
            if c:
                for dep_id in c.dependencies:
                    try:
                        deps.append(strategy.candidate_ids.index(dep_id))
                    except ValueError:
                        pass
            steps.append(SequenceStep(step_id=i + 1, candidate_id=cid, depends_on=deps))

        return ExecutionSequence(
            sequence_id=f"seq_{strategy.strategy_type}_{len(steps)}",
            steps=steps,
            total_steps=len(steps),
            strategy_type=strategy.strategy_type,
            description=strategy.description,
        )


@dataclass(frozen=True)
class PriorityAssignment:
    """Assignment prioritas."""
    candidate_id: str
    priority_score: float
    reason: str = ""


class ExecutionPriority:
    """Priority engine — prioritasi kandidat."""

    def assign(self, candidate: ExecutionCandidate) -> PriorityAssignment:
        """Assign prioritas berdasarkan effort."""
        score = max(0.0, min(1.0, 1.0 - (candidate.estimated_effort / 100.0)))
        return PriorityAssignment(
            candidate_id=candidate.candidate_id,
            priority_score=score,
            reason=f"Effort-based: {candidate.estimated_effort}",
        )

    def assign_all(self, candidates: List[ExecutionCandidate]) -> List[PriorityAssignment]:
        """Assign prioritas untuk semua kandidat."""
        return sorted(
            [self.assign(c) for c in candidates],
            key=lambda p: p.priority_score,
            reverse=True,
        )


@dataclass(frozen=True)
class ScheduleWindow:
    """Window jadwal."""
    window_id: str
    start_time: float
    end_time: float
    candidate_ids: List[str] = field(default_factory=list)


class ExecutionSchedule:
    """Schedule engine — mengatur jadwal kandidat."""

    def create_window(self, window_id: str, start: float, end: float,
                      candidates: List[ExecutionCandidate]) -> ScheduleWindow:
        """Buat window jadwal."""
        return ScheduleWindow(
            window_id=window_id,
            start_time=start,
            end_time=end,
            candidate_ids=[c.candidate_id for c in candidates],
        )
