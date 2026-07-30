"""
Decision Runtime Dashboard Gateway Bridge.

6 immutable cards for approval gateway.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class GatewayCard:
    has_result:bool; success:bool; route:str; request_id:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Gateway","has_result":self.has_result,"success":self.success,"route":self.route,"request_id":self.request_id,"timestamp":self.timestamp}
@dataclass(frozen=True)
class RegistryCard:
    total:int; ready:int; blocked:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Registry","total":self.total,"ready":self.ready,"blocked":self.blocked,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}
@dataclass(frozen=True)
class RoutingCard:
    route:str; routes_used:Dict[str,int]; supported:list; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Routing","route":self.route,"routes_used":dict(self.routes_used),"supported":list(self.supported),"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    gateway_count:int; registry_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","gateway_count":self.gateway_count,"registry_count":self.registry_count,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HealthCard:
    has_gateway:bool; default_route:str; routes_supported:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Health","has_gateway":self.has_gateway,"default_route":self.default_route,"routes_supported":self.routes_supported,"timestamp":self.timestamp}

class DecisionDashboardGatewayBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6
    def get_gateway_card(self)->GatewayCard:
        g=self._runtime._gateway; r=g.last_result if g else None
        return GatewayCard(has_result=r is not None,success=r.success if r else False,route=r.route if r else "",request_id=r.request_id if r else "",timestamp=datetime.now().timestamp())
    def get_registry_card(self)->RegistryCard:
        g=self._runtime._gateway; s=g.registry.get_statistics() if g else GatewayStatistics()
        return RegistryCard(total=s.total,ready=s.ready_count,blocked=s.blocked_count,timestamp=datetime.now().timestamp())
    def get_validation_card(self)->ValidationCard:
        g=self._runtime._gateway; r=g.last_result if g else None; v=r.validation_result if r else {"valid":True}
        return ValidationCard(valid=v.get("valid",True),errors=len(v.get("errors",[])),warnings=len(v.get("warnings",[])),score=v.get("score",1.0),timestamp=datetime.now().timestamp())
    def get_routing_card(self)->RoutingCard:
        g=self._runtime._gateway; r=g.last_result if g else None
        return RoutingCard(route=r.route if r else "none",routes_used=g.router.routes_used if g else {},supported=g.router.supported_routes if g else [],timestamp=datetime.now().timestamp())
    def get_statistics_card(self)->StatisticsCard:
        g=self._runtime._gateway
        return StatisticsCard(gateway_count=g.gateway_count if g else 0,registry_count=g.registry.count if g else 0,timestamp=datetime.now().timestamp())
    def get_health_card(self)->HealthCard:
        g=self._runtime._gateway
        return HealthCard(has_gateway=g is not None,default_route=g.registry.default_route if g else "none",routes_supported=len(g.router.supported_routes) if g else 0,timestamp=datetime.now().timestamp())
    def get_all_cards(self)->Dict[str,Any]:
        return {"gateway":self.get_gateway_card().to_dict(),"registry":self.get_registry_card().to_dict(),
                "validation":self.get_validation_card().to_dict(),"routing":self.get_routing_card().to_dict(),
                "statistics":self.get_statistics_card().to_dict(),"health":self.get_health_card().to_dict()}
