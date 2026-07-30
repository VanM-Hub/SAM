"""
Approval Runtime Adapter — Envelope DTOs.

DTO for preparing approval requests compatible with existing Approval Runtime.
Does NOT submit. Preview only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class ApprovalReference:
    preparation_id: str = ""; plan_id: str = ""; evaluation_id: str = ""
    package_id: str = ""; intent_id: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"preparation_id":self.preparation_id,"plan_id":self.plan_id,
        "evaluation_id":self.evaluation_id,"package_id":self.package_id,"intent_id":self.intent_id}

@dataclass(frozen=True)
class ApprovalPayload:
    action_type: str = ""; runtime_ids: List[str] = field(default_factory=list)
    priority: int = 0; confidence: float = 0.0
    evidence_summary: str = ""; requires_approval: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"action_type":self.action_type,"runtime_ids":list(self.runtime_ids),
        "priority":self.priority,"confidence":self.confidence,"evidence_summary":self.evidence_summary,"requires_approval":self.requires_approval}

@dataclass(frozen=True)
class ApprovalRequestEnvelope:
    envelope_id: str = ""; timestamp: float = 0.0
    references: Optional[ApprovalReference] = None
    payload: Optional[ApprovalPayload] = None
    ready: bool = False; version: str = "1.0"
    def to_dict(self) -> Dict[str,Any]: return {"envelope_id":self.envelope_id,"timestamp":self.timestamp,
        "references":self.references.to_dict() if self.references else None,
        "payload":self.payload.to_dict() if self.payload else None,"ready":self.ready,"version":self.version}

@dataclass(frozen=True)
class ApprovalEnvelopeStatistics:
    total: int = 0; ready_count: int = 0; pending_count: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"ready":self.ready_count,"pending":self.pending_count}

@dataclass(frozen=True)
class ApprovalEnvelopeSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    envelopes: List[ApprovalRequestEnvelope] = field(default_factory=list)
    statistics: Optional[ApprovalEnvelopeStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "envelopes":[e.to_dict() for e in self.envelopes],"statistics":self.statistics.to_dict() if self.statistics else None}
