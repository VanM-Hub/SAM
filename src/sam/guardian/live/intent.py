"""
Guardian Operational Intent DTOs.

Immutable DTOs for operational intent — rule-based suggestions for action.
Not actions, not missions, not execution. DTO only.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class IntentType(Enum):
    """Type of operational intent."""
    OBSERVE = auto()
    MONITOR = auto()
    ESCALATE = auto()
    RECOMMEND = auto()
    INVESTIGATE = auto()
    REVIEW = auto()
    WAIT = auto()
    NO_ACTION = auto()
    BLOCKED = auto()


class IntentPriority(Enum):
    """Priority of an operational intent."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class IntentStatus(Enum):
    """Status of an operational intent."""
    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    DISMISSED = auto()
    SUPERSEDED = auto()


@dataclass(frozen=True)
class GuardianIntent:
    """
    Immutable operational intent — a rule-based suggestion.

    NOT an action, mission, or execution.
    DTO only — no side effects.
    """

    intent_id: str
    intent_type: IntentType
    priority: IntentPriority
    status: IntentStatus
    timestamp: float
    source_assessment_id: str = ""
    source_situation_id: str = ""
    description: str = ""
    confidence: float = 0.0
    affected_runtimes: List[str] = field(default_factory=list)
    evidence_count: int = 0
    policy_name: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "intent_type": self.intent_type.name,
            "priority": self.priority.name,
            "status": self.status.name,
            "timestamp": self.timestamp,
            "source_assessment_id": self.source_assessment_id,
            "source_situation_id": self.source_situation_id,
            "description": self.description,
            "confidence": self.confidence,
            "affected_runtimes": list(self.affected_runtimes),
            "evidence_count": self.evidence_count,
            "policy_name": self.policy_name,
            "details": self.details,
        }


@dataclass(frozen=True)
class IntentSummary:
    total: int = 0
    type_counts: Dict[str, int] = field(default_factory=dict)
    priority_counts: Dict[str, int] = field(default_factory=dict)
    status_counts: Dict[str, int] = field(default_factory=dict)
    urgent_count: int = 0
    active_count: int = 0
    period_start: float = 0.0
    period_end: float = 0.0
    latest_intent: Optional[GuardianIntent] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total, "type_counts": dict(self.type_counts),
            "priority_counts": dict(self.priority_counts), "status_counts": dict(self.status_counts),
            "urgent_count": self.urgent_count, "active_count": self.active_count,
            "period_start": self.period_start, "period_end": self.period_end,
            "latest_intent": self.latest_intent.to_dict() if self.latest_intent else None,
        }


@dataclass(frozen=True)
class IntentStatistics:
    total: int = 0; by_type: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str, Any]: return {
        "total":self.total,"by_type":dict(self.by_type),"by_priority":dict(self.by_priority),
        "by_status":dict(self.by_status),"average_confidence":self.average_confidence,"timestamp":self.timestamp,
    }


@dataclass(frozen=True)
class ValidationResult:
    """Result of intent validation."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


@dataclass(frozen=True)
class IntentSnapshot:
    snapshot_id: str = ""
    timestamp: float = 0.0
    total_active: int = 0
    intents: List[GuardianIntent] = field(default_factory=list)
    highest_priority: str = "LOW"
    summary: Optional[IntentSummary] = None
    def to_dict(self) -> Dict[str, Any]: return {
        "snapshot_id":self.snapshot_id,"timestamp":self.timestamp,"total_active":self.total_active,
        "intents":[i.to_dict() for i in self.intents],"highest_priority":self.highest_priority,
        "summary":self.summary.to_dict() if self.summary else None,
    }
