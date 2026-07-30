"""
Decision Runtime Conversation Adapter Bridge.

10 DTO-only queries for approval adapter.
"""

from typing import Dict,Any,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationAdapterBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def approval_envelope(self)->Dict[str,Any]:
        l=self._runtime._bridge.last_envelope if self._runtime._bridge else None
        return {"query":"approval_envelope","has_envelope":l is not None,"envelope":l.to_dict() if l else None}
    def adapter_state(self)->Dict[str,Any]:
        b=self._runtime._bridge
        return {"query":"adapter_state","bridge_count":b.bridge_count if b else 0,"last_success":b.last_result.success if b and b.last_result else False}
    def mapping(self)->Dict[str,Any]:
        e=self._runtime._bridge.last_envelope if self._runtime._bridge else None
        return {"query":"mapping","mapped":e is not None,"ready":e.ready if e else False}
    def payload(self)->Dict[str,Any]:
        e=self._runtime._bridge.last_envelope if self._runtime._bridge else None
        return {"query":"payload","payload":e.payload.to_dict() if e and e.payload else {}}
    def status_mirror(self)->Dict[str,Any]:
        s=self._runtime._status_store
        return {"query":"status_mirror","mirror":s.latest.to_dict() if s else {},"summary":s.get_summary().to_dict() if s else {}}
    def validation(self)->Dict[str,Any]:
        b=self._runtime._bridge
        r=b.last_result if b else None
        return {"query":"validation","result":r.to_dict() if r else {"success":True}}
    def statistics(self)->Dict[str,Any]:
        return {"query":"statistics","envelopes":self._runtime._bridge.bridge_count if self._runtime._bridge else 0}
    def summary(self)->Dict[str,Any]:
        b=self._runtime._bridge; s=self._runtime._status_store
        return {"query":"summary","bridge_count":b.bridge_count if b else 0,"mirrors":s.get_summary().to_dict() if s else {}}
    def history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"history","total":self._runtime._bridge.bridge_count if self._runtime._bridge else 0}
    def readiness(self)->Dict[str,Any]:
        b=self._runtime._bridge
        return {"query":"readiness","ready":b.last_envelope.ready if b and b.last_envelope else False,
                "adapter_ok":b.last_result.success if b and b.last_result else False}
