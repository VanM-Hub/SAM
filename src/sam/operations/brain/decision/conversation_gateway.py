"""
Decision Runtime Conversation Gateway Bridge.

10 DTO-only queries for approval gateway.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationGatewayBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    def gateway(self)->Dict[str,Any]:
        r=self._runtime._gateway.last_result if self._runtime._gateway else None
        return {"query":"gateway","has_result":r is not None,"result":r.to_dict() if r else None}
    def routing(self)->Dict[str,Any]:
        g=self._runtime._gateway
        return {"query":"routing","routes_used":g.router.routes_used if g else {},"supported":g.router.supported_routes if g else []}
    def registry(self)->Dict[str,Any]:
        g=self._runtime._gateway
        return {"query":"registry","count":g.registry.count if g else 0,"stats":g.registry.get_statistics().to_dict() if g else {}}
    def request(self)->Dict[str,Any]:
        g=self._runtime._gateway; l=g.registry.last_request if g else None
        return {"query":"request","has_request":l is not None,"request":l.to_dict() if l else None}
    def validation(self)->Dict[str,Any]:
        g=self._runtime._gateway; r=g.last_result if g else None
        return {"query":"validation","result":r.validation_result if r else {"valid":True}}
    def statistics(self)->Dict[str,Any]:
        g=self._runtime._gateway
        return {"query":"statistics","gateway_count":g.gateway_count if g else 0,"registry_count":g.registry.count if g else 0}
    def summary(self)->Dict[str,Any]:
        return self.statistics()
    def history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"history","total":self._runtime._gateway.gateway_count if self._runtime._gateway else 0}
    def compatibility(self)->Dict[str,Any]:
        return {"query":"compatibility","version":"1.0","target":"ApprovalRuntime","status":"compatible"}
    def readiness(self)->Dict[str,Any]:
        g=self._runtime._gateway; r=g.last_result if g else None
        return {"query":"readiness","ready":r.success if r else False}
