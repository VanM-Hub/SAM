"""
Approval Intake Record DTOs.

Immutable intake records for Approval Runtime.
Does NOT auto-approve or auto-route. Preview only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto


class IntakeSource(Enum):
    MANUAL = auto(); DECISION_RUNTIME = auto(); API = auto(); SYSTEM = auto()


@dataclass(frozen=True)
class IntakeMetadata:
    source: IntakeSource = IntakeSource.MANUAL
    submitted_by: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    version: str = "6.0.0"
    def to_dict(self) -> Dict[str,Any]: return {"source":self.source.name,"submitted_by":self.submitted_by,
        "notes":self.notes,"tags":list(self.tags),"version":self.version}


@dataclass(frozen=True)
class ApprovalIntakeRecord:
    record_id: str = ""
    timestamp: float = 0.0
    decision_record_id: str = ""
    pipeline_version: str = ""
    readiness_score: float = 0.0
    certified: bool = False
    metadata: Optional[IntakeMetadata] = None
    payload: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str,Any]: return {"record_id":self.record_id,"timestamp":self.timestamp,
        "decision_record_id":self.decision_record_id,"pipeline_version":self.pipeline_version,
        "readiness_score":self.readiness_score,"certified":self.certified,
        "metadata":self.metadata.to_dict() if self.metadata else None}
