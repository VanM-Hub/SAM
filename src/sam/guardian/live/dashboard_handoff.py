"""
Guardian Live Dashboard Handoff Bridge.

6 immutable dashboard cards for decision handoff.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

from .decision_input import EligibilityStatus, DecisionInput

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class DecisionQueueCard:
    total: int; eligible: int; blocked: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Decision Queue","total":self.total,"eligible":self.eligible,"blocked":self.blocked,"timestamp":self.timestamp}

@dataclass(frozen=True)
class EligibleItemsCard:
    count: int; items: List[Dict[str,Any]]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Eligible Items","count":self.count,"items":list(self.items),"timestamp":self.timestamp}

@dataclass(frozen=True)
class BlockedItemsCard:
    count: int; items: List[Dict[str,Any]]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Blocked Items","count":self.count,"items":list(self.items),"timestamp":self.timestamp}

@dataclass(frozen=True)
class QueueStatisticsCard:
    total: int; eligible: int; blocked: int; avg_confidence: float; by_priority: Dict[str,int]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Queue Statistics","total":self.total,"eligible":self.eligible,"blocked":self.blocked,
                "average_confidence":self.avg_confidence,"by_priority":dict(self.by_priority),"timestamp":self.timestamp}

@dataclass(frozen=True)
class LatestHandoffCard:
    has_handoff: bool; input_id: str; eligibility: str; priority: int; confidence: float; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Latest Handoff","has_handoff":self.has_handoff,"input_id":self.input_id,
                "eligibility":self.eligibility,"priority":self.priority,"confidence":self.confidence,"timestamp":self.timestamp}

@dataclass(frozen=True)
class QueueHealthCard:
    total: int; eligible_pct: float; blocked_pct: float; avg_confidence: float; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Queue Health","total":self.total,"eligible_pct":self.eligible_pct,
                "blocked_pct":self.blocked_pct,"average_confidence":self.avg_confidence,"timestamp":self.timestamp}


class LiveDashboardHandoffBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def card_count(self) -> int:
        return 6

    def get_decision_queue_card(self) -> DecisionQueueCard:
        q = self._runtime.decision_queue
        return DecisionQueueCard(total=q.count,eligible=q.eligible_count,blocked=q.blocked_count,timestamp=datetime.now().timestamp())

    def get_eligible_items_card(self) -> EligibleItemsCard:
        q = self._runtime.decision_queue
        items = [i.to_dict() for i in q.history() if i.eligibility == EligibilityStatus.ELIGIBLE]
        return EligibleItemsCard(count=len(items),items=items[-20:],timestamp=datetime.now().timestamp())

    def get_blocked_items_card(self) -> BlockedItemsCard:
        q = self._runtime.decision_queue
        items = [i.to_dict() for i in q.history() if i.eligibility == EligibilityStatus.BLOCKED]
        return BlockedItemsCard(count=len(items),items=items[-20:],timestamp=datetime.now().timestamp())

    def get_queue_statistics_card(self) -> QueueStatisticsCard:
        q = self._runtime.decision_queue; s = q.get_statistics()
        return QueueStatisticsCard(total=s.total,eligible=s.eligible,blocked=s.blocked,avg_confidence=s.average_confidence,
                                   by_priority=s.by_priority,timestamp=datetime.now().timestamp())

    def get_latest_handoff_card(self) -> LatestHandoffCard:
        q = self._runtime.decision_queue; l = q.peek(-1)
        return LatestHandoffCard(has_handoff=l is not None,input_id=l.input_id if l else "",eligibility=l.eligibility.name if l else "",
                                 priority=l.priority_score if l else 0,confidence=l.confidence if l else 0.0,timestamp=datetime.now().timestamp())

    def get_queue_health_card(self) -> QueueHealthCard:
        q = self._runtime.decision_queue
        total = q.count or 1
        return QueueHealthCard(total=q.count,eligible_pct=round(q.eligible_count/total*100,1),
                               blocked_pct=round(q.blocked_count/total*100,1),avg_confidence=q.get_statistics().average_confidence,
                               timestamp=datetime.now().timestamp())

    def get_all_cards(self) -> Dict[str,Any]:
        return {"decision_queue":self.get_decision_queue_card().to_dict(),"eligible_items":self.get_eligible_items_card().to_dict(),
                "blocked_items":self.get_blocked_items_card().to_dict(),"queue_statistics":self.get_queue_statistics_card().to_dict(),
                "latest_handoff":self.get_latest_handoff_card().to_dict(),"queue_health":self.get_queue_health_card().to_dict()}
