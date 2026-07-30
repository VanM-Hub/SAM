"""
Guardian Live Conversation Intent Bridge.

10 DTO-only query methods for operational intent.
No async, no threading, no network.
"""

from typing import Dict, Any, TYPE_CHECKING
from datetime import datetime
from collections import defaultdict

from .intent import IntentType, IntentPriority, IntentStatus

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationIntentBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
    @property
    def query_count(self) -> int: return 10

    def latest_intent(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        l = h[-1] if h else None
        return {"query":"latest_intent","timestamp":datetime.now().timestamp(),"has_intent":l is not None,"intent":l.to_dict() if l else None}

    def intent_history(self, limit: int = 50) -> Dict[str, Any]:
        h = self._runtime.intent_history; r = h[-limit:] if limit > 0 else h
        return {"query":"intent_history","total":len(h),"returned":len(r),"intents":[i.to_dict() for i in r]}

    def intent_priority(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        pc: Dict[str,int] = defaultdict(int)
        for i in h: pc[i.priority.name] += 1
        return {"query":"intent_priority","priority_counts":dict(pc),"total":len(h)}

    def intent_policy(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        tc: Dict[str,int] = defaultdict(int)
        for i in h: tc[i.policy_name] += 1
        return {"query":"intent_policy","policy_counts":dict(tc)}

    def intent_confidence(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        if not h: return {"query":"intent_confidence","avg":0.0,"total":0}
        avg = sum(i.confidence for i in h)/len(h)
        return {"query":"intent_confidence","average":round(avg,2),"total":len(h)}

    def blocked_intent(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        b = [i for i in h if i.intent_type == IntentType.BLOCKED]
        return {"query":"blocked_intent","count":len(b),"intents":[i.to_dict() for i in b[-10:]]}

    def recommended_intent(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        r = [i for i in h if i.intent_type in (IntentType.RECOMMEND, IntentType.ESCALATE)]
        return {"query":"recommended_intent","count":len(r),"intents":[i.to_dict() for i in r[-10:]]}

    def intent_statistics(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        tc: Dict[str,int]=defaultdict(int); pc: Dict[str,int]=defaultdict(int); sc: Dict[str,int]=defaultdict(int)
        for i in h:
            tc[i.intent_type.name]+=1; pc[i.priority.name]+=1; sc[i.status.name]+=1
        return {"query":"intent_statistics","total":len(h),"by_type":dict(tc),"by_priority":dict(pc),"by_status":dict(sc)}

    def intent_summary(self) -> Dict[str, Any]:
        return self.intent_statistics()

    def current_intent(self) -> Dict[str, Any]:
        h = self._runtime.intent_history
        l = h[-1] if h else None
        return {"query":"current_intent","has_intent":l is not None,"intent":l.to_dict() if l else None}
