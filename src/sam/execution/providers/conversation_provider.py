# OP-446 — Conversation Provider Bridge
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .provider_protocol import ProviderRequest, ProviderResponse, ProviderStatus
from .provider_registry import ProviderRegistry
from .provider_router import ProviderRouter, RouteDecision, RoutingSummary
from .provider_validator import ProviderValidator, ProviderValidationReport
from sam.execution.adapters.execution_envelope import ExecutionEnvelope, ExecutionEnvelopeBuilder
from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask

@dataclass(frozen=True)
class ProviderQueryResult:
    query_type: str = ""; data: Any = None; count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationProviderBridge:
    def __init__(self, registry: ProviderRegistry, router: ProviderRouter, validator: ProviderValidator):
        self._r = registry; self._router = router; self._v = validator

    def query(self, qt: str, params: Optional[Dict]=None) -> ProviderQueryResult:
        params = params or {}
        h = {
            "provider list": self._q_list, "provider detail": self._q_detail,
            "provider health": self._q_health, "provider capability": self._q_capability,
            "routing": self._q_routing, "preview response": self._q_preview,
            "provider readiness": self._q_readiness, "provider validation": self._q_validation,
            "provider summary": self._q_summary, "provider statistics": self._q_stats,
        }
        handler = h.get(qt.lower())
        if not handler: return ProviderQueryResult(qt,{"error":f"Unknown: {qt}"},0)
        return handler(params)

    def _q_list(self, p): entries = self._r.list(); return ProviderQueryResult("provider list",
        {"providers":[{"name":e.name,"type":e.provider_type,"version":e.version,"healthy":e.healthy} for e in entries]},len(entries))

    def _q_detail(self, p):
        pid = p.get("provider_id",""); entry = self._r.find_entry(pid) if pid else None
        if not entry: return ProviderQueryResult("provider detail",{"error":"Not found"},0)
        return ProviderQueryResult("provider detail",{"name":entry.name,"type":entry.provider_type,"caps":entry.capability_names},1)

    def _q_health(self, p): s = self._r.get_statistics(); return ProviderQueryResult("provider health",
        {"healthy":s.healthy,"unhealthy":s.unhealthy,"total":s.total},s.total)

    def _q_capability(self, p):
        entries = self._r.list(); caps:Dict[str,List[str]]={}
        for e in entries:
            for c in e.capability_names: caps.setdefault(c,[]).append(e.name)
        return ProviderQueryResult("provider capability",{"capabilities":caps},len(caps))

    def _make_env(self):
        t = DispatchTask(task_id="t1",action="read",target="test"); d = DispatchRequest(tasks=(t,),requires_approval=False)
        return ExecutionEnvelopeBuilder.build(d)

    def _q_routing(self, p):
        env = self._make_env(); d = self._router.route(env,p.get("preferred_type"))
        return ProviderQueryResult("routing",{"selected":d.selected_provider_type,"passed":d.validation_passed},1)

    def _q_preview(self, p):
        env = self._make_env(); d = self._router.route(env,p.get("preferred_type"))
        resp = d.preview_response
        data = {"preview":resp.preview if resp else "","success":resp.success if resp else False} if resp else {"error":"No preview"}
        return ProviderQueryResult("preview response",data,1)

    def _q_readiness(self, p): return ProviderQueryResult("provider readiness",
        {"ready":self._r.count>0,"providers":self._r.count},1)

    def _q_validation(self, p):
        env = self._make_env(); rep = self._v.validate(env,p.get("provider_type","filesystem"))
        return ProviderQueryResult("provider validation",{"passed":rep.passed,"errors":rep.errors,"warnings":rep.warnings},rep.total_issues)

    def _q_summary(self, p): return ProviderQueryResult("provider summary",
        {"total":self._r.count,"types":len(self._r.get_statistics().by_type)})

    def _q_stats(self, p):
        s = self._r.get_statistics(); return ProviderQueryResult("provider statistics",
            {"total":s.total,"healthy":s.healthy,"unhealthy":s.unhealthy,"by_type":s.by_type},1)
