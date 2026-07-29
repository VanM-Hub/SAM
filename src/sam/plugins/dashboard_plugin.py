# OP-417 — Dashboard Plugin
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple
from .plugin_registry import PluginRegistry
from .plugin_policy import PluginPolicyEngine

@dataclass(frozen=True)
class PluginCard:
    total: int = 0; enabled: int = 0; disabled: int = 0

@dataclass(frozen=True)
class CapabilityCardP:
    total_types: int = 0; total_actions: int = 0

@dataclass(frozen=True)
class PolicyCardP:
    total: int = 0; active: int = 0; inactive: int = 0

@dataclass(frozen=True)
class HealthCardP:
    total: int = 0; healthy: int = 0; unhealthy: int = 0

@dataclass(frozen=True)
class LifecycleCard:
    total: int = 0; enabled: int = 0; disabled: int = 0

@dataclass(frozen=True)
class SummaryCardP:
    plugins: int = 0; capabilities: int = 0; policies: int = 0

@dataclass(frozen=True)
class PluginDashboard:
    plugins: PluginCard = field(default_factory=PluginCard)
    capability: CapabilityCardP = field(default_factory=CapabilityCardP)
    policy: PolicyCardP = field(default_factory=PolicyCardP)
    health: HealthCardP = field(default_factory=HealthCardP)
    lifecycle: LifecycleCard = field(default_factory=LifecycleCard)
    summary: SummaryCardP = field(default_factory=SummaryCardP)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PluginDashboardBuilder:
    @staticmethod
    def build(registry: PluginRegistry, policy: PluginPolicyEngine) -> PluginDashboard:
        s = registry.get_statistics()
        pc = PluginCard(total=s.total, enabled=s.enabled, disabled=s.disabled)
        hc = HealthCardP(total=s.total, healthy=s.healthy, unhealthy=s.unhealthy)
        entries = registry.list()
        cap_actions = sum(len(e.capability_names) for e in entries)
        cap_types = len(set(c for e in entries for c in e.capability_names))
        cc = CapabilityCardP(total_types=cap_types, total_actions=cap_actions)
        pols = policy.list_policies()
        active = sum(1 for p in pols.values() if p.get("enabled"))
        poc = PolicyCardP(total=len(pols), active=active, inactive=len(pols)-active)
        lc = LifecycleCard(total=s.total, enabled=s.enabled, disabled=s.disabled)
        sc = SummaryCardP(plugins=s.total, capabilities=cap_actions, policies=len(pols))
        return PluginDashboard(plugins=pc, capability=cc, policy=poc, health=hc, lifecycle=lc, summary=sc)
