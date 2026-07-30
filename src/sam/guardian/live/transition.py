"""
Guardian Transition DTOs.

Immutable DTOs for tracking runtime state transitions over time.
All rule-based. No AI, no machine learning.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from datetime import datetime


class TransitionType(Enum):
    """Types of runtime state transitions."""
    RUNTIME_ADDED = auto()
    RUNTIME_REMOVED = auto()
    HEALTH_CHANGED = auto()
    VERSION_CHANGED = auto()
    STATUS_CHANGED = auto()
    REGISTRY_CHANGED = auto()
    SYNC_STARTED = auto()
    SYNC_COMPLETED = auto()
    SYNC_FAILED = auto()


class ImpactLevel(Enum):
    """Impact level of a transition."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class RuntimeTransition:
    """
    Immutable record of a single runtime state transition.
    """

    transition_id: str
    transition_type: TransitionType
    runtime_id: str
    timestamp: float
    previous_state: Optional[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    impact: ImpactLevel = ImpactLevel.LOW
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "transition_type": self.transition_type.name,
            "runtime_id": self.runtime_id,
            "timestamp": self.timestamp,
            "previous_state": self.previous_state,
            "current_state": self.current_state,
            "impact": self.impact.name,
            "details": self.details,
        }


@dataclass(frozen=True)
class TransitionSummary:
    """
    Aggregated summary of transitions over a period.
    """

    total_transitions: int
    transition_counts: Dict[str, int]
    impact_counts: Dict[str, int]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    period_start: float
    period_end: float
    involved_runtimes: List[str]
    latest_transition: Optional[RuntimeTransition] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_transitions": self.total_transitions,
            "transition_counts": dict(self.transition_counts),
            "impact_counts": dict(self.impact_counts),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "involved_runtimes": list(self.involved_runtimes),
            "latest_transition": (
                self.latest_transition.to_dict()
                if self.latest_transition else None
            ),
        }


@dataclass(frozen=True)
class TransitionStatistics:
    """
    Statistical overview of transitions.
    """

    total_transitions: int
    transitions_by_type: Dict[str, int]
    transitions_by_impact: Dict[str, int]
    transitions_by_runtime: Dict[str, int]
    average_interval_seconds: float
    peak_transition_hour: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_transitions": self.total_transitions,
            "transitions_by_type": dict(self.transitions_by_type),
            "transitions_by_impact": dict(self.transitions_by_impact),
            "transitions_by_runtime": dict(self.transitions_by_runtime),
            "average_interval_seconds": self.average_interval_seconds,
            "peak_transition_hour": self.peak_transition_hour,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class TransitionHistory:
    """
    Ring buffer for transition records.
    """

    transitions: List[RuntimeTransition] = field(default_factory=list)
    max_size: int = 1000
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "max_size": self.max_size,
            "transitions": [t.to_dict() for t in self.transitions],
        }
