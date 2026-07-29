# OP-416 — Conversation Plugin Bridge
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from .plugin_registry import PluginRegistry
from .plugin_policy import PluginPolicyEngine


@dataclass(frozen=True)
class PluginQueryResult:
    query_type: str = ""; data: Any = None; count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationPluginBridge:
    """10 query types: plugin list, detail, health, capability, policy, preview,
    validation, dependency, lifecycle, diagnostics."""

    def __init__(self, registry: PluginRegistry, policy: PluginPolicyEngine):
        self._r = registry; self._pol = policy

    def query(self, qt: str, params: Optional[Dict]=None) -> PluginQueryResult:
        params = params or {}
        h = {
            "plugin list": self._q_list, "plugin detail": self._q_detail,
            "plugin health": self._q_health, "plugin capability": self._q_capability,
            "plugin policy": self._q_policy, "plugin preview": self._q_preview,
            "plugin validation": self._q_validation, "plugin dependency": self._q_dep,
            "plugin lifecycle": self._q_lifecycle, "plugin diagnostics": self._q_diag,
        }
        handler = h.get(qt.lower())
        if not handler: return PluginQueryResult(qt,{"error":f"Unknown: {qt}"},0)
        return handler(params)

    def _q_list(self, p):
        e=self._r.list(); return PluginQueryResult("plugin list",
            {"plugins":[{"name":en.name,"version":en.version,"enabled":en.enabled,"healthy":en.healthy} for en in e]},len(e))
    def _q_detail(self, p):
        pid=p.get("plugin_id",""); en=self._r.find_entry(pid) if pid else None
        if not en: return PluginQueryResult("plugin detail",{"error":"Not found"},0)
        return PluginQueryResult("plugin detail",{"name":en.name,"version":en.version,"caps":en.capability_names},1)
    def _q_health(self, p): s=self._r.get_statistics(); return PluginQueryResult("plugin health",
        {"total":s.total,"healthy":s.healthy,"unhealthy":s.unhealthy},s.total)
    def _q_capability(self, p):
        e=self._r.list(); caps:Dict[str,list]= {}
        for en in e:
            for c in en.capability_names: caps.setdefault(c,[]).append(en.name)
        return PluginQueryResult("plugin capability",{"capabilities":caps},len(caps))
    def _q_policy(self, p):
        po=self._pol.list_policies(); return PluginQueryResult("plugin policy",
            {"policies":[{"name":n,"enabled":v.get("enabled",False)} for n,v in po.items()]},len(po))
    def _q_preview(self, p): return PluginQueryResult("plugin preview",{"note":"Preview requires specific plugin ID"},0)
    def _q_validation(self, p): return PluginQueryResult("plugin validation",{"note":"Validation via Loader"},0)
    def _q_dep(self, p):
        e=self._r.list(); deps=[list(en.dependencies) for en in e if en.dependencies]
        return PluginQueryResult("plugin dependency",{"dependencies":deps},sum(len(d) for d in deps))
    def _q_lifecycle(self, p):
        s=self._r.get_statistics(); return PluginQueryResult("plugin lifecycle",
            {"enabled":s.enabled,"disabled":s.disabled,"total":s.total},1)
    def _q_diag(self, p):
        s=self._r.get_statistics(); po=self._pol.list_policies()
        return PluginQueryResult("plugin diagnostics",
            {"plugins":s.total,"enabled":s.enabled,"disabled":s.disabled,"policies":len(po)},1)
