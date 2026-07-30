"""
Decision Runtime Conversation Session Bridge.

10 DTO-only queries for approval session.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationSessionBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    def session(self)->Dict[str,Any]:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return {"query":"session","has_session":l is not None,"session":l.to_dict() if l else None}
    def registry(self)->Dict[str,Any]:
        r=self._runtime._session_registry
        return {"query":"registry","count":r.count if r else 0,"stats":r.get_statistics().to_dict() if r else {}}
    def history(self,limit:int=50)->Dict[str,Any]:
        h=self._runtime._session_history
        return {"query":"history","total":h.count if h else 0,"records":[r.to_dict() for r in h.get_all()[-limit:]] if h else []}
    def validation(self)->Dict[str,Any]:
        from .session_validator import SessionValidator
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        if not l: return {"query":"validation","valid":True}
        r=SessionValidator().validate(l); return {"query":"validation","result":r.to_dict()}
    def statistics(self)->Dict[str,Any]:
        r=self._runtime._session_registry
        return {"query":"statistics","stats":r.get_statistics().to_dict() if r else {}}
    def snapshot(self)->Dict[str,Any]:
        r=self._runtime._session_registry
        return {"query":"snapshot","snapshot":r.create_snapshot().to_dict() if r else {}}
    def references(self)->Dict[str,Any]:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return {"query":"references","refs":l.references.to_dict() if l and l.references else {}}
    def metadata(self)->Dict[str,Any]:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return {"query":"metadata","meta":l.metadata.to_dict() if l and l.metadata else {}}
    def state(self)->Dict[str,Any]:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return {"query":"state","state":l.state.name if l else "NONE"}
    def summary(self)->Dict[str,Any]:
        return self.statistics()
