"""
Decision Runtime Conversation Finalization Bridge.

10 DTO-only queries for final decision record.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationFinalizationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def finalization(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"finalization","has_record":f is not None,"record":f.to_dict() if f else None}

    def summary(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"summary","summary":f.summary.to_dict() if f and f.summary else {}}

    def record(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"record","record_id":f.record_id if f else "","state":f.state.name if f else "NONE","complete":f.complete if f else False}

    def integrity(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"integrity","score":f.pipeline_integrity if f else 0.0}

    def completion(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"completion","complete":f.complete if f else False,"state":f.state.name if f else "NONE"}

    def history(self,limit:int=50)->Dict[str,Any]:
        h=self._runtime._finalization_engine.history if self._runtime._finalization_engine else None
        return {"query":"history","total":h.count if h else 0,"records":[r.to_dict() for r in h.get_all()[-limit:]] if h else []}

    def snapshot(self)->Dict[str,Any]:
        s=self._runtime._finalization_engine.create_snapshot() if self._runtime._finalization_engine else None
        return {"query":"snapshot","snapshot":s.to_dict() if s else {}}

    def statistics(self)->Dict[str,Any]:
        s=self._runtime._finalization_engine.get_statistics() if self._runtime._finalization_engine else None
        return {"query":"statistics","stats":s.to_dict() if s else {}}

    def validation(self)->Dict[str,Any]:
        from .finalization_validator import FinalizationValidator
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        if not f: return {"query":"validation","valid":True}
        r=FinalizationValidator().validate(f); return {"query":"validation","result":r.to_dict()}

    def overview(self)->Dict[str,Any]:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return {"query":"overview","has_record":f is not None,"complete":f.complete if f else False,
                "integrity":f.pipeline_integrity if f else 0.0,
                "state":f.state.name if f else "NONE"}
