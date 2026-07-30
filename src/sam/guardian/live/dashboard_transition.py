"""
Guardian Live Dashboard Transition Bridge.

Provides 6 immutable dashboard cards for transition intelligence.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

from .transition import ImpactLevel

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class RecentChangesCard:
    """Recent transitions overview card."""
    total_transitions: int
    latest_transition_type: Optional[str]
    latest_runtime_id: Optional[str]
    latest_impact: Optional[str]
    critical_count: int
    high_count: int
    medium_count: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Recent Changes",
            "total_transitions": self.total_transitions,
            "latest_transition_type": self.latest_transition_type,
            "latest_runtime_id": self.latest_runtime_id,
            "latest_impact": self.latest_impact,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ImpactCard:
    """Current impact level card."""
    has_critical: bool
    has_high: bool
    max_impact: str
    total_transitions: int
    impact_summary: Dict[str, int]
    recommendations: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Impact",
            "has_critical": self.has_critical,
            "has_high": self.has_high,
            "max_impact": self.max_impact,
            "total_transitions": self.total_transitions,
            "impact_summary": dict(self.impact_summary),
            "recommendations": list(self.recommendations),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TimelineCard:
    """Timeline overview card."""
    total_events: int
    transition_types: Dict[str, int]
    period_start: float
    period_end: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Timeline",
            "total_events": self.total_events,
            "transition_types": dict(self.transition_types),
            "period_start": self.period_start,
            "period_end": self.period_end,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class CriticalEventsCard:
    """Critical and high-impact events card."""
    critical_count: int
    high_count: int
    recent_critical: List[Dict[str, Any]]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Critical Events",
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "recent_critical": list(self.recent_critical),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TransitionStatisticsCard:
    """Transition statistics overview card."""
    total_transitions: int
    by_type: Dict[str, int]
    by_impact: Dict[str, int]
    by_runtime: Dict[str, int]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Transition Statistics",
            "total_transitions": self.total_transitions,
            "by_type": dict(self.by_type),
            "by_impact": dict(self.by_impact),
            "by_runtime": dict(self.by_runtime),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class RuntimeEvolutionCard:
    """Runtime evolution over time card."""
    runtimes_count: int
    added_runtimes: int
    removed_runtimes: int
    changed_runtimes: int
    health_changes: int
    version_changes: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Runtime Evolution",
            "runtimes_count": self.runtimes_count,
            "added_runtimes": self.added_runtimes,
            "removed_runtimes": self.removed_runtimes,
            "changed_runtimes": self.changed_runtimes,
            "health_changes": self.health_changes,
            "version_changes": self.version_changes,
            "timestamp": self.timestamp,
        }


class LiveDashboardTransitionBridge:
    """
    Bridge for transition dashboard cards.

    Provides 6 immutable cards:
        1. Recent Changes
        2. Impact
        3. Timeline
        4. Critical Events
        5. Transition Statistics
        6. Runtime Evolution
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def card_count(self) -> int:
        return 6

    def get_recent_changes_card(self) -> RecentChangesCard:
        latest = self._runtime.timeline.latest
        summary = self._runtime.timeline.get_summary()
        return RecentChangesCard(
            total_transitions=summary.total_transitions,
            latest_transition_type=latest.transition_type.name if latest else None,
            latest_runtime_id=latest.runtime_id if latest else None,
            latest_impact=latest.impact.name if latest else None,
            critical_count=summary.critical_count,
            high_count=summary.high_count,
            medium_count=summary.medium_count,
            timestamp=datetime.now().timestamp(),
        )

    def get_impact_card(self) -> ImpactCard:
        all_t = self._runtime.timeline.get_all()
        result = self._runtime.impact_analyzer.analyze_batch(all_t)
        return ImpactCard(
            has_critical=result["has_critical"],
            has_high=result["has_high"],
            max_impact=result["max_impact"],
            total_transitions=result["total"],
            impact_summary=result.get("impact_summary", {}),
            recommendations=result.get("recommendations", []),
            timestamp=datetime.now().timestamp(),
        )

    def get_timeline_card(self) -> TimelineCard:
        summary = self._runtime.timeline.get_summary()
        return TimelineCard(
            total_events=summary.total_transitions,
            transition_types=summary.transition_counts,
            period_start=summary.period_start,
            period_end=summary.period_end,
            timestamp=datetime.now().timestamp(),
        )

    def get_critical_events_card(self) -> CriticalEventsCard:
        critical = self._runtime.timeline.filter(min_impact=ImpactLevel.HIGH, limit=10)
        return CriticalEventsCard(
            critical_count=sum(1 for t in critical if t.impact == ImpactLevel.CRITICAL),
            high_count=sum(1 for t in critical if t.impact == ImpactLevel.HIGH),
            recent_critical=[t.to_dict() for t in critical],
            timestamp=datetime.now().timestamp(),
        )

    def get_transition_statistics_card(self) -> TransitionStatisticsCard:
        stats = self._runtime.timeline.get_statistics()
        return TransitionStatisticsCard(
            total_transitions=stats.total_transitions,
            by_type=stats.transitions_by_type,
            by_impact=stats.transitions_by_impact,
            by_runtime=stats.transitions_by_runtime,
            timestamp=datetime.now().timestamp(),
        )

    def get_runtime_evolution_card(self) -> RuntimeEvolutionCard:
        all_t = self._runtime.timeline.get_all()
        added = sum(1 for t in all_t if t.transition_type.name == "RUNTIME_ADDED")
        removed = sum(1 for t in all_t if t.transition_type.name == "RUNTIME_REMOVED")
        changed = sum(1 for t in all_t if t.transition_type.name in (
            "HEALTH_CHANGED", "VERSION_CHANGED", "STATUS_CHANGED"
        ))
        health = sum(1 for t in all_t if t.transition_type.name == "HEALTH_CHANGED")
        version_c = sum(1 for t in all_t if t.transition_type.name == "VERSION_CHANGED")
        return RuntimeEvolutionCard(
            runtimes_count=self._runtime.registry.count,
            added_runtimes=added,
            removed_runtimes=removed,
            changed_runtimes=changed,
            health_changes=health,
            version_changes=version_c,
            timestamp=datetime.now().timestamp(),
        )

    def get_all_cards(self) -> Dict[str, Any]:
        return {
            "recent_changes": self.get_recent_changes_card().to_dict(),
            "impact": self.get_impact_card().to_dict(),
            "timeline": self.get_timeline_card().to_dict(),
            "critical_events": self.get_critical_events_card().to_dict(),
            "transition_statistics": self.get_transition_statistics_card().to_dict(),
            "runtime_evolution": self.get_runtime_evolution_card().to_dict(),
        }
