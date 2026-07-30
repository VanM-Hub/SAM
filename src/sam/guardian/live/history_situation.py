"""
Guardian Situation History.

Ring buffer for tracking situations over time.
Synchronous only. No async, no threading, no network.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from .situation import (
    GuardianSituation, SituationType, SituationSeverity,
    SituationSummary, SituationStatistics,
)


class SituationHistory:
    """
    Ring buffer for situation history.

    Stores situations with a max size.
    Supports lookup, history, latest, statistics, summary.
    """

    def __init__(self, max_size: int = 500) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[GuardianSituation]] = [None] * max_size
        self._head: int = 0
        self._count: int = 0

    def record(self, situation: GuardianSituation) -> None:
        """Record a situation."""
        self._buffer[self._head] = situation
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size:
            self._count += 1

    def record_batch(self, situations: List[GuardianSituation]) -> None:
        """Record multiple situations."""
        for s in situations:
            self.record(s)

    @property
    def latest(self) -> Optional[GuardianSituation]:
        """Get the most recent situation."""
        if self._count == 0:
            return None
        idx = (self._head - 1) % self._max_size
        return self._buffer[idx]

    @property
    def current(self) -> Optional[GuardianSituation]:
        """Get the current (most recent) situation."""
        return self.latest

    @property
    def count(self) -> int:
        return self._count

    def get_all(self) -> List[GuardianSituation]:
        """Get all situations in chronological order."""
        if self._count == 0:
            return []
        if self._count < self._max_size:
            records = self._buffer[:self._count]
        else:
            records = (
                self._buffer[self._head:] + self._buffer[:self._head]
            )
        return [s for s in records if s is not None]

    def lookup(self, situation_id: str) -> Optional[GuardianSituation]:
        """Find a situation by ID."""
        for s in self.get_all():
            if s.situation_id == situation_id:
                return s
        return None

    def filter(
        self,
        situation_type: Optional[SituationType] = None,
        min_severity: Optional[SituationSeverity] = None,
        max_severity: Optional[SituationSeverity] = None,
        runtime_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[GuardianSituation]:
        """Filter situations by criteria."""
        results = self.get_all()

        if situation_type:
            results = [s for s in results if s.situation_type == situation_type]
        if min_severity:
            results = [
                s for s in results
                if s.severity.value >= min_severity.value
            ]
        if max_severity:
            results = [
                s for s in results
                if s.severity.value <= max_severity.value
            ]
        if runtime_id:
            results = [
                s for s in results
                if runtime_id in s.affected_runtimes
            ]
        if limit and limit > 0:
            results = results[-limit:]

        return results

    def get_summary(self) -> SituationSummary:
        """Get aggregated summary of all situations."""
        all_situations = self.get_all()
        now = datetime.now().timestamp()

        type_counts: Dict[str, int] = defaultdict(int)
        severity_counts: Dict[str, int] = defaultdict(int)

        for s in all_situations:
            type_counts[s.situation_type.name] += 1
            severity_counts[s.severity.name] += 1

        period_start = all_situations[0].timestamp if all_situations else now
        period_end = now

        return SituationSummary(
            total_situations=len(all_situations),
            type_counts=dict(type_counts),
            severity_counts=dict(severity_counts),
            critical_count=severity_counts.get("CRITICAL", 0),
            high_count=severity_counts.get("HIGH", 0),
            medium_count=severity_counts.get("MEDIUM", 0),
            low_count=severity_counts.get("LOW", 0),
            info_count=severity_counts.get("INFO", 0),
            period_start=period_start,
            period_end=period_end,
            latest_situation=self.latest,
        )

    def get_statistics(self) -> SituationStatistics:
        """Get statistical overview."""
        all_situations = self.get_all()

        type_counts: Dict[str, int] = defaultdict(int)
        severity_counts: Dict[str, int] = defaultdict(int)
        runtime_counts: Dict[str, int] = defaultdict(int)

        total_duration = 0.0

        for s in all_situations:
            type_counts[s.situation_type.name] += 1
            severity_counts[s.severity.name] += 1
            for rid in s.affected_runtimes:
                runtime_counts[rid] += 1
            total_duration += s.duration_seconds

        avg_duration = 0.0
        if all_situations:
            avg_duration = total_duration / len(all_situations)

        return SituationStatistics(
            total_situations=len(all_situations),
            by_type=dict(type_counts),
            by_severity=dict(severity_counts),
            by_runtime=dict(runtime_counts),
            average_duration_seconds=round(avg_duration, 4),
            timestamp=datetime.now().timestamp(),
        )

    def clear(self) -> None:
        """Clear all situations."""
        self._buffer = [None] * self._max_size
        self._head = 0
        self._count = 0

    def is_full(self) -> bool:
        return self._count == self._max_size
