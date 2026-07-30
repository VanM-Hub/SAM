"""
Finalization DTOs.

Immutable final decision record — end of Decision Runtime pipeline.
Does NOT execute approval. Preview only.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto


class FinalDecisionState(Enum):
    PENDING = auto(); FINALIZED = auto(); COMPLETED = auto()
    INVALIDATED = auto(); ARCHIVED = auto(); REOPENED = auto()


@dataclass(frozen=True)
class FinalDecisionSummary:
    pipeline_stages: int = 0; total_checks: int = 0; checks_passed: int = 0
    readiness_score: float = 0.0; certification_state: str = ""
    evidence_count: int = 0; blocker_count: int = 0
    activation_state: str = ""; lifecycle_state: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"pipeline_stages":self.pipeline_stages,"total_checks":self.total_checks,
        "checks_passed":self.checks_passed,"readiness_score":self.readiness_score,
        "certification_state":self.certification_state,"evidence_count":self.evidence_count,
        "blocker_count":self.blocker_count,"activation_state":self.activation_state,"lifecycle_state":self.lifecycle_state}

@dataclass(frozen=True)
class FinalDecisionMetadata:
    record_id: str = ""; created_at: float = 0.0; version: str = "5.20.0"
    source_pipeline: str = "DecisionRuntime"; target: str = "ApprovalRuntime"
    def to_dict(self) -> Dict[str,Any]: return {"record_id":self.record_id,"created_at":self.created_at,
        "version":self.version,"source_pipeline":self.source_pipeline,"target":self.target}

@dataclass(frozen=True)
class FinalDecisionRecord:
    record_id: str = ""; timestamp: float = 0.0
    state: FinalDecisionState = FinalDecisionState.PENDING
    session_id: str = ""; lifecycle_id: str = ""; activation_id: str = ""
    certification_id: str = ""; gateway_request_id: str = ""
    summary: Optional[FinalDecisionSummary] = None
    metadata: Optional[FinalDecisionMetadata] = None
    pipeline_integrity: float = 0.0; complete: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"record_id":self.record_id,"timestamp":self.timestamp,
        "state":self.state.name,"session_id":self.session_id,"lifecycle_id":self.lifecycle_id,
        "activation_id":self.activation_id,"certification_id":self.certification_id,
        "gateway_request_id":self.gateway_request_id,"summary":self.summary.to_dict() if self.summary else None,
        "metadata":self.metadata.to_dict() if self.metadata else None,
        "pipeline_integrity":self.pipeline_integrity,"complete":self.complete}

@dataclass(frozen=True)
class FinalDecisionStatistics:
    total: int = 0; pending: int = 0; finalized: int = 0
    completed: int = 0; invalidated: int = 0; archived: int = 0; reopened: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"pending":self.pending,"finalized":self.finalized,
        "completed":self.completed,"invalidated":self.invalidated,"archived":self.archived,"reopened":self.reopened}

@dataclass(frozen=True)
class FinalDecisionSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    records: List[FinalDecisionRecord] = field(default_factory=list)
    statistics: Optional[FinalDecisionStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "records":[r.to_dict() for r in self.records],
        "statistics":self.statistics.to_dict() if self.statistics else None}
