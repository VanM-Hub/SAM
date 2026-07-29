# OP-407 — Dashboard Integration
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple
from .registry import IntegrationRegistry
from .policy import IntegrationPolicyEngine

@dataclass(frozen=True)
class ProviderCard:
    total: int = 0; healthy: int = 0; unhealthy: int = 0
    by_type: Dict[str,int] = field(default_factory=dict)

@dataclass(frozen=True)
class HealthCard:
    overall_healthy: bool = True; total: int = 0; healthy: int = 0; unhealthy: int = 0

@dataclass(frozen=True)
class CapabilityCard:
    total_types: int = 0; total_capabilities: int = 0
    types: Tuple[str,...] = field(default_factory=tuple)

@dataclass(frozen=True)
class PolicyCard:
    total: int = 0; active: int = 0; inactive: int = 0

@dataclass(frozen=True)
class PlanCard:
    total_plans: int = 0; avg_duration: int = 0; avg_risk: str = ""

@dataclass(frozen=True)
class SummaryCard:
    providers: int = 0; capabilities: int = 0; plans: int = 0; policies: int = 0

@dataclass(frozen=True)
class IntegrationDashboard:
    providers: ProviderCard = field(default_factory=ProviderCard)
    health: HealthCard = field(default_factory=HealthCard)
    capability: CapabilityCard = field(default_factory=CapabilityCard)
    policy: PolicyCard = field(default_factory=PolicyCard)
    plan: PlanCard = field(default_factory=PlanCard)
    summary: SummaryCard = field(default_factory=SummaryCard)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DashboardIntegrationBuilder:
    @staticmethod
    def build(registry: IntegrationRegistry, policy: IntegrationPolicyEngine, plans: int = 0) -> IntegrationDashboard:
        s = registry.get_statistics()
        pc = ProviderCard(total=s.total,healthy=s.healthy,unhealthy=s.unhealthy,by_type=s.by_type)
        hc = HealthCard(overall_healthy=s.unhealthy==0,total=s.total,healthy=s.healthy,unhealthy=s.unhealthy)
        entries = registry.list(); types = tuple(e.integration_type for e in entries)
        total_caps = sum(len(e.capability_names) for e in entries)
        cc = CapabilityCard(total_types=len(set(types)),total_capabilities=total_caps,types=types)
        pols = policy.list_policies()
        active = sum(1 for p in pols.values() if p.get("enabled"))
        inactive = len(pols)-active
        poc = PolicyCard(total=len(pols),active=active,inactive=inactive)
        pc2 = PlanCard(total_plans=plans)
        sc = SummaryCard(providers=s.total,capabilities=total_caps,plans=plans,policies=len(pols))
        return IntegrationDashboard(providers=pc,health=hc,capability=cc,policy=poc,plan=pc2,summary=sc)
