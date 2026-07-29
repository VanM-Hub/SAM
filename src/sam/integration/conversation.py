# OP-406 — Conversation Integration Bridge
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .contracts import IntegrationRequest
from .registry import IntegrationRegistry
from .policy import IntegrationPolicyEngine, PolicyResult
from .planner import IntegrationPlanner, IntegrationPlan


@dataclass(frozen=True)
class IntegrationQueryResult:
    query_type: str = ""; data: Any = None; count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationIntegrationBridge:
    """10 query types: list integrations, integration health, preview integration,
    capabilities, connector status, policy, approval requirement,
    integration plan, available providers, diagnostics."""

    def __init__(self, registry: IntegrationRegistry, planner: IntegrationPlanner,
                 policy: IntegrationPolicyEngine):
        self._r = registry; self._p = planner; self._pol = policy

    def query(self, qt: str, params: Optional[Dict]=None) -> IntegrationQueryResult:
        params = params or {}
        h = {
            "list integrations": self._q_list,
            "integration health": self._q_health,
            "preview integration": self._q_preview,
            "capabilities": self._q_capabilities,
            "connector status": self._q_status,
            "policy": self._q_policy,
            "approval requirement": self._q_approval,
            "integration plan": self._q_plan,
            "available providers": self._q_providers,
            "diagnostics": self._q_diagnostics,
        }
        handler = h.get(qt.lower())
        if not handler: return IntegrationQueryResult(qt,{"error":f"Unknown: {qt}"},0)
        return handler(params)

    def _q_list(self, p): e=self._r.list(); return IntegrationQueryResult("list integrations",
        {"providers":[{"name":en.name,"type":en.integration_type,"healthy":en.healthy} for en in e]},len(e))
    def _q_health(self, p): s=self._r.get_statistics(); return IntegrationQueryResult("integration health",
        {"healthy":s.healthy,"unhealthy":s.unhealthy,"total":s.total},s.total)
    def _q_preview(self, p):
        req=IntegrationRequest(integration_type=p.get("type","slack"),action=p.get("action","notify"),
            target=p.get("target","general"),payload=p.get("payload",{}))
        provs=self._r.find_by_type(req.integration_type)
        if provs: resp=provs[0].preview(req); data={"summary":resp.preview.summary if resp.preview else "","success":resp.success}
        else: data={"error":"Provider not found"}
        return IntegrationQueryResult("preview integration",data,1)
    def _q_capabilities(self, p):
        e=self._r.list(); caps:Dict[str,List[str]]={}
        for en in e:
            for c in en.capability_names: caps.setdefault(c,[]).append(en.name)
        return IntegrationQueryResult("capabilities",{"capabilities":caps},len(caps))
    def _q_status(self, p): return IntegrationQueryResult("connector status",{"count":self._r.count},self._r.count)
    def _q_policy(self, p): po=self._pol.list_policies(); return IntegrationQueryResult("policy",
        {"policies":[{"name":n,"enabled":v.get("enabled",False)} for n,v in po.items()]},len(po))
    def _q_approval(self, p):
        risk=p.get("risk","medium")
        r=self._pol.evaluate(action=p.get("action","read"),risk_level=risk)
        return IntegrationQueryResult("approval requirement",
            {"requires_approval":not r.approved,"risk":risk,"violations":list(r.violations)},1)
    def _q_plan(self, p):
        req=IntegrationRequest(integration_type=p.get("type","slack"),action=p.get("action","notify"),target=p.get("target","general"))
        plan=self._p.plan(req); return IntegrationQueryResult("integration plan",
            {"steps":plan.total_steps,"duration":plan.estimated_duration,"risk":plan.aggregated_risk,
             "approval":plan.requires_approval},plan.total_steps)
    def _q_providers(self, p):
        types=list(self._r.get_statistics().by_type.keys())
        return IntegrationQueryResult("available providers",{"types":types},len(types))
    def _q_diagnostics(self, p):
        s=self._r.get_statistics(); po=self._pol.list_policies()
        return IntegrationQueryResult("diagnostics",{"providers":s.total,"healthy":s.healthy,
            "unhealthy":s.unhealthy,"policies":len(po)},1)
