"""
Approval Session DTOs.

Immutable session representation for one approval process.
Does NOT execute approval. Preview only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto


class ApprovalSessionState(Enum):
    CREATED = auto(); VALIDATED = auto(); PENDING = auto()
    ACTIVE = auto(); COMPLETED = auto(); CLOSED = auto(); CANCELLED = auto()


@dataclass(frozen=True)
class ApprovalSessionReference:
    gateway_request_id: str = ""; submission_plan_id: str = ""
    envelope_id: str = ""; plan_id: str = ""; evaluation_id: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"gateway_request_id":self.gateway_request_id,"submission_plan_id":self.submission_plan_id,
        "envelope_id":self.envelope_id,"plan_id":self.plan_id,"evaluation_id":self.evaluation_id}

@dataclass(frozen=True)
class ApprovalSessionMetadata:
    session_id: str = ""; created_at: float = 0.0; version: str = "1.0"
    source_component: str = "DecisionRuntime"; target_component: str = "ApprovalRuntime"
    def to_dict(self) -> Dict[str,Any]: return {"session_id":self.session_id,"created_at":self.created_at,"version":self.version,
        "source_component":self.source_component,"target_component":self.target_component}

@dataclass(frozen=True)
class ApprovalSession:
    session_id: str = ""; timestamp: float = 0.0
    state: ApprovalSessionState = ApprovalSessionState.CREATED
    references: Optional[ApprovalSessionReference] = None
    metadata: Optional[ApprovalSessionMetadata] = None
    payload: Optional[Dict[str, Any]] = None
    ready: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"session_id":self.session_id,"timestamp":self.timestamp,
        "state":self.state.name,"references":self.references.to_dict() if self.references else None,
        "metadata":self.metadata.to_dict() if self.metadata else None,"payload":self.payload,"ready":self.ready}

@dataclass(frozen=True)
class ApprovalSessionStatistics:
    total: int = 0; created: int = 0; validated: int = 0
    pending: int = 0; active: int = 0; completed: int = 0; closed: int = 0; cancelled: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"created":self.created,"validated":self.validated,
        "pending":self.pending,"active":self.active,"completed":self.completed,"closed":self.closed,"cancelled":self.cancelled}

@dataclass(frozen=True)
class ApprovalSessionSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    sessions: List[ApprovalSession] = field(default_factory=list)
    statistics: Optional[ApprovalSessionStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "sessions":[s.to_dict() for s in self.sessions],"statistics":self.statistics.to_dict() if self.statistics else None}
