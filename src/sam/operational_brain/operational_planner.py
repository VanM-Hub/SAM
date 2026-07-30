"""Operational Planner — memprioritaskan dan mengurutkan kandidat.

Planner menerima kandidat dari Builder dan menghasilkan plan entry yang terurut.
Tidak memutuskan apa yang dieksekusi — hanya mengatur prioritas.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List

from sam.operational_brain.operational_candidate import OperationalCandidate
from sam.operational_brain.operational_context import OperationalContext


class PriorityTier(Enum):
    """Tier prioritas untuk operational plan."""
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()
    BACKGROUND = auto()


@dataclass(frozen=True)
class PlanEntry:
    """Satu entry dalam operational plan — immutable."""
    entry_id: str
    candidate: OperationalCandidate
    priority_tier: PriorityTier
    priority_score: float       # 0.0–1.0 composite
    rank: int                   # 1-based, 1 = tertinggi
    reason: str
    metadata: Dict[str, object] = field(default_factory=dict)


class OperationalPrioritizer:
    """Memprioritaskan kandidat berdasarkan konteks dan skor."""

    def prioritize(self, candidates: List[OperationalCandidate],
                   ctx: OperationalContext) -> List[PlanEntry]:
        """Urutkan kandidat berdasarkan prioritas."""
        entries: List[PlanEntry] = []
        for c in candidates:
            ps = self._composite_score(c, ctx)
            tier = self._determine_tier(c, ps)
            entries.append(PlanEntry(
                entry_id=f"plan_{c.candidate_id}",
                candidate=c,
                priority_tier=tier,
                priority_score=round(ps, 4),
                rank=0,  # assigned after sorting
                reason=f"score={ps:.3f} tier={tier.name}",
            ))

        # sort descending by priority_score
        entries.sort(key=lambda e: e.priority_score, reverse=True)
        # assign 1-based rank
        ranked = [
            PlanEntry(
                entry_id=e.entry_id,
                candidate=e.candidate,
                priority_tier=e.priority_tier,
                priority_score=e.priority_score,
                rank=i + 1,
                reason=e.reason,
                metadata=e.metadata,
            )
            for i, e in enumerate(entries)
        ]
        return ranked

    def _composite_score(self, c: OperationalCandidate,
                         ctx: OperationalContext) -> float:
        """Compute composite priority score 0.0–1.0."""
        w_score = 0.35 * c.score
        w_urgency = 0.30 * c.urgency
        w_impact = 0.20 * c.impact
        w_confidence = 0.15 * c.confidence
        # reduce for high effort
        effort_penalty = 0.10 * c.effort
        raw = w_score + w_urgency + w_impact + w_confidence - effort_penalty
        return max(0.0, min(1.0, raw))

    def _determine_tier(self, c: OperationalCandidate,
                        ps: float) -> PriorityTier:
        if c.candidate_id == "c_rec":
            return PriorityTier.CRITICAL
        if ps >= 0.70:
            return PriorityTier.HIGH
        if ps >= 0.40:
            return PriorityTier.MEDIUM
        if ps >= 0.15:
            return PriorityTier.LOW
        return PriorityTier.BACKGROUND


@dataclass(frozen=True)
class PlanSummary:
    """Ringkasan operational plan."""
    total_entries: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    background: int = 0
    top_score: float = 0.0
    bottom_score: float = 0.0


class OperationalPlanner:
    """Planner mengorkestrasi prioritisasi dan menghasilkan ringkasan."""

    def __init__(self, prioritizer: OperationalPrioritizer = None):
        self._prioritizer = prioritizer or OperationalPrioritizer()
        self._entries: List[PlanEntry] = []

    @property
    def entries(self) -> List[PlanEntry]:
        return list(self._entries)

    def plan(self, candidates: List[OperationalCandidate],
             ctx: OperationalContext) -> List[PlanEntry]:
        """Generate prioritized plan dari candidates."""
        self._entries = self._prioritizer.prioritize(candidates, ctx)
        return list(self._entries)

    def summary(self) -> PlanSummary:
        entries = self._entries
        if not entries:
            return PlanSummary()
        critical = sum(1 for e in entries if e.priority_tier == PriorityTier.CRITICAL)
        high = sum(1 for e in entries if e.priority_tier == PriorityTier.HIGH)
        medium = sum(1 for e in entries if e.priority_tier == PriorityTier.MEDIUM)
        low = sum(1 for e in entries if e.priority_tier == PriorityTier.LOW)
        background = sum(1 for e in entries if e.priority_tier == PriorityTier.BACKGROUND)
        return PlanSummary(
            total_entries=len(entries),
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            background=background,
            top_score=entries[0].priority_score,
            bottom_score=entries[-1].priority_score,
        )

    def plan_dict(self) -> Dict[str, object]:
        s = self.summary()
        return {
            "total_entries": s.total_entries,
            "critical": s.critical,
            "high": s.high,
            "medium": s.medium,
            "low": s.low,
            "background": s.background,
            "top_score": round(s.top_score, 4),
            "bottom_score": round(s.bottom_score, 4),
        }
