"""
Decision Runtime Conversation Activation Bridge.

10 DTO-only queries for activation preview.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationActivationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def activation(self)->Dict[str,Any]:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return {"query":"activation","has_activation":a is not None,"activation":a.to_dict() if a else None}

    def state(self)->Dict[str,Any]:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return {"query":"state","state":a.state.name if a else "NONE"}

    def decision(self)->Dict[str,Any]:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return {"query":"decision","decision":a.decision.name if a else "NONE"}

    def blockers(self)->Dict[str,Any]:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return {"query":"blockers","count":len(a.blockers) if a else 0,"blockers":list(a.blockers) if a else []}

    def history(self,limit:int=50)->Dict[str,Any]:
        h=self._runtime._activation_engine.history if self._runtime._activation_engine else None
        return {"query":"history","total":h.count if h else 0,"records":[r.to_dict() for r in h.get_all()[-limit:]] if h else []}

    def statistics(self)->Dict[str,Any]:
        s=self._runtime._activation_engine.get_statistics() if self._runtime._activation_engine else None
        return {"query":"statistics","stats":s.to_dict() if s else {}}

    def snapshot(self)->Dict[str,Any]:
        s=self._runtime._activation_engine.create_snapshot() if self._runtime._activation_engine else None
        return {"query":"snapshot","snapshot":s.to_dict() if s else {}}

    def rules(self)->Dict[str,Any]:
        from .activation_rules import ActivationRules
        return {"query":"rules","states":["PENDING","EVALUATED","READY","BLOCKED","INVALID","WAITING"]}

    def validation(self)->Dict[str,Any]:
        from .activation_validator import ActivationValidator
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        if not a: return {"query":"validation","valid":True}
        r=ActivationValidator().validate(a); return {"query":"validation","result":r.to_dict()}

    def summary(self)->Dict[str,Any]:
        return self.statistics()
