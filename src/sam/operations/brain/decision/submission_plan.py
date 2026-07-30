"""
Approval Submission Plan DTOs.

Immutable DTOs for orchestrating approval submission.
Does NOT submit. Preview only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class SubmissionReference:
    envelope_id: str = ""; plan_id: str = ""; evaluation_id: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"envelope_id":self.envelope_id,"plan_id":self.plan_id,"evaluation_id":self.evaluation_id}

@dataclass(frozen=True)
class SubmissionMetadata:
    submission_id: str = ""; created_at: float = 0.0; version: str = "1.0"
    depends_on: List[str] = field(default_factory=list); priority: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"submission_id":self.submission_id,"created_at":self.created_at,"version":self.version,"depends_on":list(self.depends_on),"priority":self.priority}

@dataclass(frozen=True)
class SubmissionStage:
    name: str = ""; status: str = ""; result: Optional[Dict[str,Any]] = None
    def to_dict(self) -> Dict[str,Any]: return {"name":self.name,"status":self.status,"result":self.result}

@dataclass(frozen=True)
class ApprovalSubmissionPlan:
    plan_id: str = ""; timestamp: float = 0.0; envelope_id: str = ""
    metadata: Optional[SubmissionMetadata] = None
    references: Optional[SubmissionReference] = None
    stages: List[SubmissionStage] = field(default_factory=list)
    ready: bool = False; summary: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"plan_id":self.plan_id,"timestamp":self.timestamp,"envelope_id":self.envelope_id,
        "metadata":self.metadata.to_dict() if self.metadata else None,"references":self.references.to_dict() if self.references else None,
        "stages":[s.to_dict() for s in self.stages],"ready":self.ready,"summary":self.summary}

@dataclass(frozen=True)
class SubmissionStatistics:
    total: int = 0; ready_count: int = 0; blocked_count: int = 0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"ready":self.ready_count,"blocked":self.blocked_count,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SubmissionSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    plans: List[ApprovalSubmissionPlan] = field(default_factory=list)
    statistics: Optional[SubmissionStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "plans":[p.to_dict() for p in self.plans],"statistics":self.statistics.to_dict() if self.statistics else None}
