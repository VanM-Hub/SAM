"""
Approval Activation DTOs.

Immutable activation preview for Approval Sessions.
Does NOT execute approval. Preview only.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto


class ActivationState(Enum):
    PENDING = auto(); EVALUATED = auto(); READY = auto()
    BLOCKED = auto(); INVALID = auto(); WAITING = auto()


class ActivationDecision(Enum):
    APPROVE = auto(); REJECT = auto(); HOLD = auto(); ESCALATE = auto(); NONE = auto()


@dataclass(frozen=True)
class ApprovalActivation:
    activation_id: str = ""; lifecycle_id: str = ""; session_id: str = ""
    timestamp: float = 0.0
    state: ActivationState = ActivationState.PENDING
    decision: ActivationDecision = ActivationDecision.NONE
    blockers: List[str] = field(default_factory=list)
    readiness_score: float = 0.0
    ready: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"activation_id":self.activation_id,"lifecycle_id":self.lifecycle_id,
        "session_id":self.session_id,"timestamp":self.timestamp,"state":self.state.name,
        "decision":self.decision.name,"blockers":list(self.blockers),
        "readiness_score":self.readiness_score,"ready":self.ready}

@dataclass(frozen=True)
class ActivationMetadata:
    activation_id: str = ""; created_at: float = 0.0; version: str = "1.0"
    source: str = "DecisionRuntime"; target: str = "ApprovalRuntime"
    def to_dict(self) -> Dict[str,Any]: return {"activation_id":self.activation_id,"created_at":self.created_at,
        "version":self.version,"source":self.source,"target":self.target}

@dataclass(frozen=True)
class ActivationStatistics:
    total: int = 0; pending: int = 0; evaluated: int = 0
    ready: int = 0; blocked: int = 0; invalid: int = 0; waiting: int = 0
    approved: int = 0; rejected: int = 0; held: int = 0; escalated: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"pending":self.pending,"evaluated":self.evaluated,
        "ready":self.ready,"blocked":self.blocked,"invalid":self.invalid,"waiting":self.waiting,
        "approved":self.approved,"rejected":self.rejected,"held":self.held,"escalated":self.escalated}

@dataclass(frozen=True)
class ActivationSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    activations: List[ApprovalActivation] = field(default_factory=list)
    statistics: Optional[ActivationStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "activations":[a.to_dict() for a in self.activations],
        "statistics":self.statistics.to_dict() if self.statistics else None}
