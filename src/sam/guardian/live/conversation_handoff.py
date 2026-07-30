"""
Guardian Live Conversation Handoff Bridge.

10 DTO-only query methods for decision handoff.
No async, no threading, no network.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime

from .decision_input import EligibilityStatus

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationHandoffBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def query_count(self) -> int:
        return 10

    def decision_queue(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        return {"query":"decision_queue","count":q.count,"eligible":q.eligible_count,"blocked":q.blocked_count,
                "latest":q.peek().to_dict() if q.count>0 else None}

    def latest_handoff(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        l = q.peek(-1)
        return {"query":"latest_handoff","has_handoff":l is not None,"handoff":l.to_dict() if l else None}

    def eligible_decisions(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        items = [i.to_dict() for i in q.history() if i.eligibility == EligibilityStatus.ELIGIBLE]
        return {"query":"eligible_decisions","count":len(items),"decisions":items[-20:]}

    def blocked_decisions(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        items = [i.to_dict() for i in q.history() if i.eligibility == EligibilityStatus.BLOCKED]
        return {"query":"blocked_decisions","count":len(items),"decisions":items[-20:]}

    def handoff_history(self, limit: int = 50) -> Dict[str, Any]:
        h = self._runtime.decision_queue.history(limit)
        return {"query":"handoff_history","total":self._runtime.decision_queue.count,"returned":len(h),
                "handoffs":[i.to_dict() for i in h]}

    def queue_statistics(self) -> Dict[str, Any]:
        s = self._runtime.decision_queue.get_statistics()
        return {"query":"queue_statistics","statistics":s.to_dict()}

    def priority_queue(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        items = sorted(q.history(), key=lambda i: -i.priority_score)
        return {"query":"priority_queue","count":len(items),"items":[i.to_dict() for i in items[:20]]}

    def mapping(self) -> Dict[str, Any]:
        from .mapping import IntentMapper
        m = IntentMapper()
        return {"query":"mapping","action_map":list(IntentMapper._ACTION_MAP.values()) if hasattr(IntentMapper,'_ACTION_MAP') else []}

    def eligibility(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        return {"query":"eligibility","total":q.count,"eligible":q.eligible_count,"blocked":q.blocked_count}

    def summary(self) -> Dict[str, Any]:
        q = self._runtime.decision_queue
        s = q.get_statistics()
        l = q.peek(-1)
        return {"query":"summary","queue_count":q.count,"statistics":s.to_dict(),"latest":l.to_dict() if l else None}
