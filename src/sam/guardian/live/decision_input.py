"""
Guardian Decision Input DTOs.

Immutable DTOs for handing off operational intent to Decision Runtime.
Does NOT call Decision Runtime. Builds DTO only.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class EligibilityStatus(Enum):
    """Status of decision eligibility."""
    ELIGIBLE = auto()
    NOT_ELIGIBLE = auto()
    BLOCKED = auto()
    PENDING = auto()


@dataclass(frozen=True)
class DecisionMetadata:
    source_intent_id: str = ""
    source_assessment_id: str = ""
    source_situation_id: str = ""
    handoff_timestamp: float = 0.0
    version: str = "1.0"
    def to_dict(self) -> Dict[str, Any]:
        return {"source_intent_id":self.source_intent_id,"source_assessment_id":self.source_assessment_id,
                "source_situation_id":self.source_situation_id,"handoff_timestamp":self.handoff_timestamp,"version":self.version}

@dataclass(frozen=True)
class DecisionCandidate:
    candidate_id: str = ""
    runtime_id: str = ""
    action_type: str = ""
    priority: int = 0
    confidence: float = 0.0
    evidence_count: int = 0
    details: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str, Any]:
        return {"candidate_id":self.candidate_id,"runtime_id":self.runtime_id,"action_type":self.action_type,
                "priority":self.priority,"confidence":self.confidence,"evidence_count":self.evidence_count,"details":self.details}

@dataclass(frozen=True)
class DecisionReason:
    primary: str = ""
    details: List[str] = field(default_factory=list)
    rules_triggered: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return {"primary":self.primary,"details":list(self.details),"rules_triggered":list(self.rules_triggered)}

@dataclass(frozen=True)
class DecisionInput:
    input_id: str = ""
    timestamp: float = 0.0
    metadata: Optional[DecisionMetadata] = None
    candidates: List[DecisionCandidate] = field(default_factory=list)
    reason: Optional[DecisionReason] = None
    eligibility: EligibilityStatus = EligibilityStatus.PENDING
    confidence: float = 0.0
    priority_score: int = 0
    def to_dict(self) -> Dict[str, Any]:
        return {"input_id":self.input_id,"timestamp":self.timestamp,
                "metadata":self.metadata.to_dict() if self.metadata else None,
                "candidates":[c.to_dict() for c in self.candidates],
                "reason":self.reason.to_dict() if self.reason else None,
                "eligibility":self.eligibility.name,"confidence":self.confidence,"priority_score":self.priority_score}

@dataclass(frozen=True)
class DecisionStatistics:
    total: int = 0; eligible: int = 0; blocked: int = 0
    by_priority: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str, Any]: return {"total":self.total,"eligible":self.eligible,"blocked":self.blocked,
        "by_priority":dict(self.by_priority),"average_confidence":self.average_confidence,"timestamp":self.timestamp}

@dataclass(frozen=True)
class DecisionSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0; total_queue: int = 0
    decisions: List[DecisionInput] = field(default_factory=list); statistics: Optional[DecisionStatistics] = None
    def to_dict(self) -> Dict[str, Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "total_queue":self.total_queue,"decisions":[d.to_dict() for d in self.decisions],
        "statistics":self.statistics.to_dict() if self.statistics else None}
