"""
Decision Runtime Conversation Lifecycle Bridge.

10 DTO-only queries for approval lifecycle.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationLifecycleBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def lifecycle(self)->Dict[str,Any]:
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        return {"query":"lifecycle","has_lifecycle":l is not None,"lifecycle":l.to_dict() if l else None}

    def state(self)->Dict[str,Any]:
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        return {"query":"state","state":l.state.name if l else "NONE"}

    def transition(self)->Dict[str,Any]:
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        if not l or not l.transitions: return {"query":"transitions","count":0,"last":{}}
        return {"query":"transitions","count":len(l.transitions),"last":l.transitions[-1].to_dict()}

    def history(self,limit:int=50)->Dict[str,Any]:
        h=self._runtime._lifecycle_engine.history if self._runtime._lifecycle_engine else None
        return {"query":"history","total":h.count if h else 0,"records":[r.to_dict() for r in h.get_all()[-limit:]] if h else []}

    def rules(self)->Dict[str,Any]:
        from .lifecycle_rules import LifecycleRules
        return {"query":"rules","states":["CREATED","VALIDATED","READY","WAITING","CANCELLED","CLOSED"]}

    def statistics(self)->Dict[str,Any]:
        s=self._runtime._lifecycle_engine.get_statistics() if self._runtime._lifecycle_engine else None
        return {"query":"statistics","stats":s.to_dict() if s else {}}

    def snapshot(self)->Dict[str,Any]:
        s=self._runtime._lifecycle_engine.create_snapshot() if self._runtime._lifecycle_engine else None
        return {"query":"snapshot","snapshot":s.to_dict() if s else {}}

    def validation(self)->Dict[str,Any]:
        from .lifecycle_validator import LifecycleValidator
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        if not l: return {"query":"validation","valid":True}
        r=LifecycleValidator().validate(l); return {"query":"validation","result":r.to_dict()}

    def timeline(self)->Dict[str,Any]:
        h=self._runtime._lifecycle_engine.history if self._runtime._lifecycle_engine else None
        records=h.get_all() if h else []
        return {"query":"timeline","total":len(records),"first":records[0].to_dict() if records else None,"last":records[-1].to_dict() if records else None}

    def summary(self)->Dict[str,Any]:
        return self.statistics()
