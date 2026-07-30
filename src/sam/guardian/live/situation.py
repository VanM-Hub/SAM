"""
Guardian Situation DTOs.

Immutable DTOs for operational situations derived from transitions.
All rule-based, deterministic. No AI, no machine learning.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from datetime import datetime


class SituationType(Enum):
    """Built-in situation types. All rule-based."""
    HEALTHY = auto()
    BUSY = auto()
    APPROVAL_BOTTLENECK = auto()
    EXECUTION_DELAY = auto()
    RUNTIME_INSTABILITY = auto()
    RECOVERY = auto()
    CONFIGURATION_DRIFT = auto()
    RESOURCE_PRESSURE = auto()
    UNKNOWN = auto()


class SituationSeverity(Enum):
    """Severity level of an operational situation."""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class GuardianSituation:
    """
    Immutable representation of an operational situation.

    A situation is a group of related transitions that share
    common characteristics (time, runtime, severity, etc.)
    """

    situation_id: str
    situation_type: SituationType
    severity: SituationSeverity
    timestamp: float
    duration_seconds: float = 0.0
    related_transition_ids: List[str] = field(default_factory=list)
    affected_runtimes: List[str] = field(default_factory=list)
    description: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "situation_id": self.situation_id,
            "situation_type": self.situation_type.name,
            "severity": self.severity.name,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "related_transition_ids": list(self.related_transition_ids),
            "affected_runtimes": list(self.affected_runtimes),
            "description": self.description,
            "details": self.details,
        }


@dataclass(frozen=True)
class SituationSummary:
    """Aggregated summary of situations over time."""
    total_situations: int
    type_counts: Dict[str, int]
    severity_counts: Dict[str, int]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    period_start: float
    period_end: float
    latest_situation: Optional[GuardianSituation] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_situations": self.total_situations,
            "type_counts": dict(self.type_counts),
            "severity_counts": dict(self.severity_counts),
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "latest_situation": (
                self.latest_situation.to_dict()
                if self.latest_situation else None
            ),
        }


@dataclass(frozen=True)
class SituationStatistics:
    """Statistical overview of situations."""
    total_situations: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_runtime: Dict[str, int]
    average_duration_seconds: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_situations": self.total_situations,
            "by_type": dict(self.by_type),
            "by_severity": dict(self.by_severity),
            "by_runtime": dict(self.by_runtime),
            "average_duration_seconds": self.average_duration_seconds,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SituationCandidate:
    """
    A potential situation being built from related transitions.
    Not yet classified — intermediate DTO.
    """
    transition_ids: List[str]
    runtimes: List[str]
    score: float = 0.0
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_ids": list(self.transition_ids),
            "runtimes": list(self.runtimes),
            "score": self.score,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SituationSnapshot:
    """
    Point-in-time view of all active situations.
    """
    snapshot_id: str
    timestamp: float
    total_active: int
    situations: List[GuardianSituation]
    highest_severity: str
    summary: SituationSummary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "total_active": self.total_active,
            "situations": [s.to_dict() for s in self.situations],
            "highest_severity": self.highest_severity,
            "summary": self.summary.to_dict(),
        }
