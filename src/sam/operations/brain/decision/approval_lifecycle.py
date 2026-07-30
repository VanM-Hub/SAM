"""
Approval Lifecycle DTOs.

Immutable lifecycle representation for Approval Sessions.
Does NOT execute approval. Preview only.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto


class ApprovalLifecycleState(Enum):
    CREATED = auto(); VALIDATED = auto(); READY = auto()
    WAITING = auto(); CANCELLED = auto(); CLOSED = auto()


@dataclass(frozen=True)
class LifecycleTransition:
    from_state: str; to_state: str; timestamp: float = 0.0
    reason: str = ""; triggered_by: str = "lifecycle_engine"
    def to_dict(self) -> Dict[str,Any]: return {"from":self.from_state,"to":self.to_state,
        "timestamp":self.timestamp,"reason":self.reason,"triggered_by":self.triggered_by}

@dataclass(frozen=True)
class ApprovalLifecycle:
    lifecycle_id: str = ""; session_id: str = ""; timestamp: float = 0.0
    state: ApprovalLifecycleState = ApprovalLifecycleState.CREATED
    transitions: List[LifecycleTransition] = field(default_factory=list)
    session_ready: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"lifecycle_id":self.lifecycle_id,"session_id":self.session_id,
        "timestamp":self.timestamp,"state":self.state.name,"transitions":[t.to_dict() for t in self.transitions],
        "session_ready":self.session_ready}

@dataclass(frozen=True)
class LifecycleMetadata:
    lifecycle_id: str = ""; created_at: float = 0.0; version: str = "1.0"
    target_component: str = "ApprovalRuntime"; current_state: str = "CREATED"
    def to_dict(self) -> Dict[str,Any]: return {"lifecycle_id":self.lifecycle_id,"created_at":self.created_at,
        "version":self.version,"target_component":self.target_component,"current_state":self.current_state}

@dataclass(frozen=True)
class LifecycleStatistics:
    total: int = 0; created: int = 0; validated: int = 0
    ready: int = 0; waiting: int = 0; cancelled: int = 0; closed: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"created":self.created,"validated":self.validated,
        "ready":self.ready,"waiting":self.waiting,"cancelled":self.cancelled,"closed":self.closed}

@dataclass(frozen=True)
class LifecycleSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    lifecycles: List[ApprovalLifecycle] = field(default_factory=list)
    statistics: Optional[LifecycleStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "lifecycles":[l.to_dict() for l in self.lifecycles],"statistics":self.statistics.to_dict() if self.statistics else None}
