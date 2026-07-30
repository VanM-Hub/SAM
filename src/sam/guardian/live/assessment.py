"""
Guardian Assessment DTOs.

Immutable DTOs for operational assessment of runtime situations.
All deterministic, rule-based. No AI.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class AssessmentLevel(Enum):
    """Level of an assessment finding."""
    POSITIVE = auto()
    INFO = auto()
    WARNING = auto()
    CONCERN = auto()
    CRITICAL = auto()


class AssessmentCategory(Enum):
    """Category of assessment."""
    OVERALL_HEALTH = auto()
    OPERATIONAL_RISK = auto()
    EXECUTION_RISK = auto()
    APPROVAL_RISK = auto()
    RUNTIME_RISK = auto()
    CONSISTENCY_RISK = auto()
    RECOVERY_RISK = auto()
    PERFORMANCE = auto()
    STABILITY = auto()
    SECURITY = auto()


class RiskLevel(Enum):
    """Risk level for a specific dimension."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class PriorityLevel(Enum):
    """Priority level for assessment findings."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass(frozen=True)
class GuardianAssessment:
    """
    Immutable operational assessment of runtime situation.

    Converts situations and transitions into actionable
    assessments. Deterministic, rule-based.
    """

    assessment_id: str
    timestamp: float
    situation_id: str
    category: AssessmentCategory
    level: AssessmentLevel
    risk: RiskLevel
    priority: PriorityLevel
    confidence: float
    description: str
    affected_runtimes: List[str] = field(default_factory=list)
    evidence_count: int = 0
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp,
            "situation_id": self.situation_id,
            "category": self.category.name,
            "level": self.level.name,
            "risk": self.risk.name,
            "priority": self.priority.name,
            "confidence": self.confidence,
            "description": self.description,
            "affected_runtimes": list(self.affected_runtimes),
            "evidence_count": self.evidence_count,
            "details": self.details,
        }


@dataclass(frozen=True)
class AssessmentSummary:
    """Aggregated summary of assessments."""
    total_assessments: int
    category_counts: Dict[str, int]
    level_counts: Dict[str, int]
    risk_counts: Dict[str, int]
    priority_counts: Dict[str, int]
    critical_count: int
    warning_count: int
    confident_count: int
    period_start: float
    period_end: float
    latest_assessment: Optional[GuardianAssessment] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_assessments": self.total_assessments,
            "category_counts": dict(self.category_counts),
            "level_counts": dict(self.level_counts),
            "risk_counts": dict(self.risk_counts),
            "priority_counts": dict(self.priority_counts),
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "confident_count": self.confident_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "latest_assessment": (
                self.latest_assessment.to_dict()
                if self.latest_assessment else None
            ),
        }


@dataclass(frozen=True)
class AssessmentStatistics:
    """Statistical overview of assessments."""
    total: int
    by_category: Dict[str, int]
    by_level: Dict[str, int]
    by_risk: Dict[str, int]
    by_priority: Dict[str, int]
    average_confidence: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_category": dict(self.by_category),
            "by_level": dict(self.by_level),
            "by_risk": dict(self.by_risk),
            "by_priority": dict(self.by_priority),
            "average_confidence": self.average_confidence,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class AssessmentSnapshot:
    """Point-in-time snapshot of all assessments."""
    snapshot_id: str
    timestamp: float
    total_active: int
    assessments: List[GuardianAssessment]
    highest_risk: str
    highest_priority: str
    summary: AssessmentSummary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "total_active": self.total_active,
            "assessments": [a.to_dict() for a in self.assessments],
            "highest_risk": self.highest_risk,
            "highest_priority": self.highest_priority,
            "summary": self.summary.to_dict(),
        }
