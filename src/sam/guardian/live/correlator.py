"""
Guardian Transition Correlator.

Correlates transitions into situation candidates based on rules.
All deterministic, rule-based. No AI.
Synchronous only.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict

from .transition import RuntimeTransition, TransitionType, ImpactLevel
from .situation import GuardianSituation, SituationType, SituationSeverity, SituationCandidate


class TransitionCorrelator:
    """
    Rule-based correlator that groups related transitions into situations.

    Correlation rules:
        - Time proximity (transitions within a time window)
        - Shared runtime (same runtime involved)
        - Shared severity (same impact level)
        - Shared component (same component type)
        - Shared source (same transition type)
    """

    def __init__(self, time_window_seconds: float = 60.0) -> None:
        self._time_window = time_window_seconds

    def correlate(
        self,
        transitions: List[RuntimeTransition],
    ) -> List[SituationCandidate]:
        """
        Correlate transitions into situation candidates.

        Args:
            transitions: List of transitions to correlate.

        Returns:
            List of SituationCandidate (not yet classified).
        """
        if not transitions:
            return []

        candidates: List[SituationCandidate] = []
        used_ids: Set[str] = set()

        # 1. Group by time proximity
        time_groups = self._group_by_time(transitions)
        for group in time_groups:
            group_ids = [t.transition_id for t in group]
            runtimes = list(set(t.runtime_id for t in group))
            score = self._calculate_score(group)

            candidate = SituationCandidate(
                transition_ids=group_ids,
                runtimes=runtimes,
                score=score,
                reason=self._determine_reason(group),
            )

            # Mark transition IDs as used
            for tid in group_ids:
                used_ids.add(tid)

            candidates.append(candidate)

        # 2. Correlate unused transitions by shared runtime
        remaining = [t for t in transitions if t.transition_id not in used_ids]
        remaining_by_runtime = self._group_by_runtime(remaining)
        for rid, group in remaining_by_runtime.items():
            group_ids = [t.transition_id for t in group]
            runtimes = [rid]
            score = 0.5

            candidate = SituationCandidate(
                transition_ids=group_ids,
                runtimes=runtimes,
                score=score,
                reason=f"Runtime correlation: {rid}",
            )
            for tid in group_ids:
                used_ids.add(tid)
            candidates.append(candidate)

        # Sort by score descending
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    def _group_by_time(
        self,
        transitions: List[RuntimeTransition],
    ) -> List[List[RuntimeTransition]]:
        """Group transitions that occur within the time window."""
        sorted_transitions = sorted(transitions, key=lambda t: t.timestamp)
        groups: List[List[RuntimeTransition]] = []
        current_group: List[RuntimeTransition] = []

        for t in sorted_transitions:
            if not current_group:
                current_group.append(t)
            else:
                time_diff = t.timestamp - current_group[0].timestamp
                if time_diff <= self._time_window:
                    current_group.append(t)
                else:
                    groups.append(current_group)
                    current_group = [t]

        if current_group:
            groups.append(current_group)

        return groups

    def _group_by_runtime(
        self,
        transitions: List[RuntimeTransition],
    ) -> Dict[str, List[RuntimeTransition]]:
        """Group transitions by runtime ID."""
        groups: Dict[str, List[RuntimeTransition]] = defaultdict(list)
        for t in transitions:
            groups[t.runtime_id].append(t)
        return dict(groups)

    def _calculate_score(self, transitions: List[RuntimeTransition]) -> float:
        """
        Calculate correlation score for a group of transitions.

        Score factors:
            - Number of transitions
            - Presence of CRITICAL/HIGH impact
            - Number of affected runtimes
        """
        if not transitions:
            return 0.0

        score = 0.0

        # Base score from count
        score += min(len(transitions) * 0.2, 2.0)

        # Impact bonus
        for t in transitions:
            if t.impact == ImpactLevel.CRITICAL:
                score += 1.0
            elif t.impact == ImpactLevel.HIGH:
                score += 0.5

        # Runtime diversity bonus
        unique_runtimes = len(set(t.runtime_id for t in transitions))
        if unique_runtimes > 1:
            score += min(unique_runtimes * 0.3, 1.5)

        return round(score, 4)

    def _determine_reason(
        self,
        transitions: List[RuntimeTransition],
    ) -> str:
        """Determine the reason for this correlation."""
        types = set(t.transition_type.name for t in transitions)
        runtimes = set(t.runtime_id for t in transitions)
        return (
            f"{len(transitions)} transitions across "
            f"{len(runtimes)} runtime(s) "
            f"({', '.join(sorted(types))})"
        )
