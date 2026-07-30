"""
Guardian Live Dashboard Situation Bridge.

Provides 6 immutable dashboard cards for situation intelligence.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

from .situation import SituationSeverity

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class CurrentSituationCard:
    type_name: str; severity: str; description: str; related_transitions: int
    affected_runtimes: List[str]; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Current Situation","type":self.type_name,"severity":self.severity,
                "description":self.description,"related_transitions":self.related_transitions,
                "affected_runtimes":list(self.affected_runtimes),"timestamp":self.timestamp}

@dataclass(frozen=True)
class SituationTimelineCard:
    total: int; types: Dict[str,int]; period_start: float; period_end: float; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Situation Timeline","total":self.total,"types":dict(self.types),
                "period_start":self.period_start,"period_end":self.period_end,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SituationSeverityCard:
    current_severity: str; severity_counts: Dict[str,int]; highest: str; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Situation Severity","current_severity":self.current_severity,
                "severity_counts":dict(self.severity_counts),"highest":self.highest,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SituationStatisticsCard:
    total: int; by_type: Dict[str,int]; avg_duration: float; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Situation Statistics","total":self.total,"by_type":dict(self.by_type),
                "avg_duration_seconds":self.avg_duration,"timestamp":self.timestamp}

@dataclass(frozen=True)
class RuntimeDistributionCard:
    total: int; runtime_counts: Dict[str,int]; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Runtime Distribution","total":self.total,
                "runtime_counts":dict(self.runtime_counts),"timestamp":self.timestamp}

@dataclass(frozen=True)
class SituationHistoryCard:
    total: int; critical: int; high: int; medium: int; low: int; info: int; timestamp: float
    def to_dict(self) -> Dict[str, Any]:
        return {"card":"Situation History","total":self.total,"critical":self.critical,
                "high":self.high,"medium":self.medium,"low":self.low,"info":self.info,"timestamp":self.timestamp}


class LiveDashboardSituationBridge:
    """6 immutable cards for situation dashboard."""

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def card_count(self) -> int:
        return 6

    def get_current_situation_card(self) -> CurrentSituationCard:
        s = self._runtime.situation_history.latest
        return CurrentSituationCard(
            type_name=s.situation_type.name if s else "NONE",
            severity=s.severity.name if s else "NONE",
            description=s.description if s else "No situation data",
            related_transitions=len(s.related_transition_ids) if s else 0,
            affected_runtimes=list(s.affected_runtimes) if s else [],
            timestamp=datetime.now().timestamp(),
        )

    def get_situation_timeline_card(self) -> SituationTimelineCard:
        summary = self._runtime.situation_history.get_summary()
        return SituationTimelineCard(
            total=summary.total_situations,
            types=summary.type_counts,
            period_start=summary.period_start,
            period_end=summary.period_end,
            timestamp=datetime.now().timestamp(),
        )

    def get_situation_severity_card(self) -> SituationSeverityCard:
        s = self._runtime.situation_history.latest
        summary = self._runtime.situation_history.get_summary()
        return SituationSeverityCard(
            current_severity=s.severity.name if s else "NONE",
            severity_counts=summary.severity_counts,
            highest=max(summary.severity_counts.keys()) if summary.severity_counts else "NONE",
            timestamp=datetime.now().timestamp(),
        )

    def get_situation_statistics_card(self) -> SituationStatisticsCard:
        stats = self._runtime.situation_history.get_statistics()
        return SituationStatisticsCard(
            total=stats.total_situations,
            by_type=stats.by_type,
            avg_duration=stats.average_duration_seconds,
            timestamp=datetime.now().timestamp(),
        )

    def get_runtime_distribution_card(self) -> RuntimeDistributionCard:
        stats = self._runtime.situation_history.get_statistics()
        return RuntimeDistributionCard(
            total=stats.total_situations,
            runtime_counts=stats.by_runtime,
            timestamp=datetime.now().timestamp(),
        )

    def get_situation_history_card(self) -> SituationHistoryCard:
        summary = self._runtime.situation_history.get_summary()
        return SituationHistoryCard(
            total=summary.total_situations,
            critical=summary.critical_count,
            high=summary.high_count,
            medium=summary.medium_count,
            low=summary.low_count,
            info=summary.info_count,
            timestamp=datetime.now().timestamp(),
        )

    def get_all_cards(self) -> Dict[str, Any]:
        return {
            "current_situation": self.get_current_situation_card().to_dict(),
            "situation_timeline": self.get_situation_timeline_card().to_dict(),
            "situation_severity": self.get_situation_severity_card().to_dict(),
            "situation_statistics": self.get_situation_statistics_card().to_dict(),
            "runtime_distribution": self.get_runtime_distribution_card().to_dict(),
            "situation_history": self.get_situation_history_card().to_dict(),
        }
