"""
Guardian Transition Timeline.

Ring buffer for tracking runtime transitions over time.
Synchronous only. No async, no threading, no network.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from .transition import (
    RuntimeTransition,
    TransitionType,
    ImpactLevel,
    TransitionSummary,
    TransitionStatistics,
)


class TransitionTimeline:
    """
    Ring buffer for transition history.

    Stores transitions in chronological order with a max size.
    """

    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[RuntimeTransition]] = [None] * max_size
        self._head: int = 0
        self._count: int = 0

    def record(self, transition: RuntimeTransition) -> None:
        """Record a transition."""
        self._buffer[self._head] = transition
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size:
            self._count += 1

    def record_batch(self, transitions: List[RuntimeTransition]) -> None:
        """Record multiple transitions."""
        for t in transitions:
            self.record(t)

    @property
    def latest(self) -> Optional[RuntimeTransition]:
        """Get the most recent transition."""
        if self._count == 0:
            return None
        idx = (self._head - 1) % self._max_size
        return self._buffer[idx]

    @property
    def count(self) -> int:
        return self._count

    def get_all(self) -> List[RuntimeTransition]:
        """Get all transitions in chronological order."""
        if self._count == 0:
            return []
        if self._count < self._max_size:
            records = self._buffer[:self._count]
        else:
            records = (
                self._buffer[self._head:] + self._buffer[:self._head]
            )
        return [r for r in records if r is not None]

    def lookup(self, transition_id: str) -> Optional[RuntimeTransition]:
        """Find a transition by ID."""
        for t in self.get_all():
            if t.transition_id == transition_id:
                return t
        return None

    def filter(
        self,
        transition_type: Optional[TransitionType] = None,
        impact: Optional[ImpactLevel] = None,
        runtime_id: Optional[str] = None,
        min_impact: Optional[ImpactLevel] = None,
        limit: Optional[int] = None,
    ) -> List[RuntimeTransition]:
        """Filter transitions by criteria."""
        results = self.get_all()

        if transition_type:
            results = [t for t in results if t.transition_type == transition_type]
        if impact:
            results = [t for t in results if t.impact == impact]
        if runtime_id:
            results = [t for t in results if t.runtime_id == runtime_id]
        if min_impact:
            results = [
                t for t in results
                if t.impact.value >= min_impact.value
            ]
        if limit and limit > 0:
            results = results[-limit:]

        return results

    def get_summary(self) -> TransitionSummary:
        """Get aggregated summary of current transitions."""
        all_transitions = self.get_all()
        now = datetime.now().timestamp()

        type_counts: Dict[str, int] = defaultdict(int)
        impact_counts: Dict[str, int] = defaultdict(int)
        runtimes: Dict[str, int] = defaultdict(int)

        for t in all_transitions:
            type_counts[t.transition_type.name] += 1
            impact_counts[t.impact.name] += 1
            runtimes[t.runtime_id] += 1

        period_start = 0.0
        period_end = now
        if all_transitions:
            period_start = all_transitions[0].timestamp - 0.001

        return TransitionSummary(
            total_transitions=len(all_transitions),
            transition_counts=dict(type_counts),
            impact_counts=dict(impact_counts),
            critical_count=impact_counts.get("CRITICAL", 0),
            high_count=impact_counts.get("HIGH", 0),
            medium_count=impact_counts.get("MEDIUM", 0),
            low_count=impact_counts.get("LOW", 0),
            period_start=period_start,
            period_end=period_end,
            involved_runtimes=list(runtimes.keys()),
            latest_transition=self.latest,
        )

    def get_statistics(self) -> TransitionStatistics:
        """Get statistical overview."""
        all_transitions = self.get_all()

        type_counts: Dict[str, int] = defaultdict(int)
        impact_counts: Dict[str, int] = defaultdict(int)
        runtime_counts: Dict[str, int] = defaultdict(int)

        for t in all_transitions:
            type_counts[t.transition_type.name] += 1
            impact_counts[t.impact.name] += 1
            runtime_counts[t.runtime_id] += 1

        avg_interval = 0.0
        if len(all_transitions) > 1:
            total_time = (
                all_transitions[-1].timestamp - all_transitions[0].timestamp
            )
            avg_interval = total_time / (len(all_transitions) - 1)

        return TransitionStatistics(
            total_transitions=len(all_transitions),
            transitions_by_type=dict(type_counts),
            transitions_by_impact=dict(impact_counts),
            transitions_by_runtime=dict(runtime_counts),
            average_interval_seconds=round(avg_interval, 4),
            peak_transition_hour=now().hour if False else 0,
            timestamp=datetime.now().timestamp(),
        )

    def clear(self) -> None:
        """Clear all transitions."""
        self._buffer = [None] * self._max_size
        self._head = 0
        self._count = 0

    def is_full(self) -> bool:
        return self._count == self._max_size
