"""
Guardian Live Dashboard Intent Bridge.

6 immutable dashboard cards for operational intent.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

from .intent import IntentType, IntentPriority

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class CurrentIntentCard:
    type_name: str; priority: str; confidence: float; description: str; affected: List[str]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Current Intent","type":self.type_name,"priority":self.priority,"confidence":self.confidence,"description":self.description,"affected_runtimes":list(self.affected),"timestamp":self.timestamp}

@dataclass(frozen=True)
class IntentQueueCard:
    total: int; urgent: int; high: int; normal: int; low: int; by_type: Dict[str,int]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Intent Queue","total":self.total,"urgent":self.urgent,"high":self.high,"normal":self.normal,"low":self.low,"by_type":dict(self.by_type),"timestamp":self.timestamp}

@dataclass(frozen=True)
class IntentPriorityCard:
    priority_counts: Dict[str,int]; highest: str; total: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Intent Priority","priority_counts":dict(self.priority_counts),"highest":self.highest,"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class IntentPoliciesCard:
    policy_counts: Dict[str,int]; total: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Intent Policies","policy_counts":dict(self.policy_counts),"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class IntentValidationCard:
    total_valid: int; total_invalid: int; errors: int; warnings: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Intent Validation","total_valid":self.total_valid,"total_invalid":self.total_invalid,"errors":self.errors,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class IntentHistoryCard:
    total: int; by_type: Dict[str,int]; by_priority: Dict[str,int]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Intent History","total":self.total,"by_type":dict(self.by_type),"by_priority":dict(self.by_priority),"timestamp":self.timestamp}


class LiveDashboardIntentBridge:
    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
    @property
    def card_count(self) -> int: return 6

    def get_current_intent_card(self) -> CurrentIntentCard:
        h = self._runtime.intent_history; l = h[-1] if h else None
        return CurrentIntentCard(type_name=l.intent_type.name if l else "NONE",priority=l.priority.name if l else "NONE",
            confidence=l.confidence if l else 0.0,description=l.description if l else "",affected=list(l.affected_runtimes) if l else [],timestamp=datetime.now().timestamp())

    def get_intent_queue_card(self) -> IntentQueueCard:
        h = self._runtime.intent_history
        tc: Dict[str,int]=defaultdict(int); urg=high=norm=low=0
        for i in h:
            tc[i.intent_type.name]+=1
            if i.priority==IntentPriority.URGENT: urg+=1
            elif i.priority==IntentPriority.HIGH: high+=1
            elif i.priority==IntentPriority.NORMAL: norm+=1
            else: low+=1
        return IntentQueueCard(total=len(h),urgent=urg,high=high,normal=norm,low=low,by_type=dict(tc),timestamp=datetime.now().timestamp())

    def get_intent_priority_card(self) -> IntentPriorityCard:
        h = self._runtime.intent_history
        pc: Dict[str,int]=defaultdict(int); hst="LOW"
        for i in h:
            pc[i.priority.name]+=1
        return IntentPriorityCard(priority_counts=dict(pc),highest=hst,total=len(h),timestamp=datetime.now().timestamp())

    def get_intent_policies_card(self) -> IntentPoliciesCard:
        h = self._runtime.intent_history
        pc: Dict[str,int]=defaultdict(int)
        for i in h: pc[i.policy_name]+=1
        return IntentPoliciesCard(policy_counts=dict(pc),total=len(h),timestamp=datetime.now().timestamp())

    def get_intent_validation_card(self) -> IntentValidationCard:
        return IntentValidationCard(total_valid=0,total_invalid=0,errors=0,warnings=0,timestamp=datetime.now().timestamp())

    def get_intent_history_card(self) -> IntentHistoryCard:
        h = self._runtime.intent_history
        tc: Dict[str,int]=defaultdict(int); pc: Dict[str,int]=defaultdict(int)
        for i in h: tc[i.intent_type.name]+=1; pc[i.priority.name]+=1
        return IntentHistoryCard(total=len(h),by_type=dict(tc),by_priority=dict(pc),timestamp=datetime.now().timestamp())

    def get_all_cards(self) -> Dict[str,Any]:
        return {
            "current_intent":self.get_current_intent_card().to_dict(),"intent_queue":self.get_intent_queue_card().to_dict(),
            "intent_priority":self.get_intent_priority_card().to_dict(),"intent_policies":self.get_intent_policies_card().to_dict(),
            "intent_validation":self.get_intent_validation_card().to_dict(),"intent_history":self.get_intent_history_card().to_dict(),
        }
