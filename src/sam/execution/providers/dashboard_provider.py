# OP-447 — Dashboard Provider
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple

from .provider_registry import ProviderRegistry
from .provider_router import RoutingSummary
from .provider_protocol import ProviderResponse


@dataclass(frozen=True)
class ProviderCard:
    total: int = 0; healthy: int = 0; unhealthy: int = 0
    by_type: Dict[str,int] = field(default_factory=dict)

@dataclass(frozen=True)
class ProviderHealthCard:
    overall_healthy: bool = True; total: int = 0; healthy: int = 0; unhealthy: int = 0

@dataclass(frozen=True)
class CapabilityCard3:
    total_types: int = 0; total_capabilities: int = 0
    types: Tuple[str,...] = field(default_factory=tuple)

@dataclass(frozen=True)
class RoutingCard:
    total_decisions: int = 0; success_rate: float = 0.0
    provider_types: Tuple[str,...] = field(default_factory=tuple)

@dataclass(frozen=True)
class PreviewCard3:
    last_preview: str = ""; success: bool = False; provider_type: str = ""

@dataclass(frozen=True)
class StatisticsCard3:
    total_providers: int = 0; total_capabilities: int = 0; avg_health: float = 0.0

@dataclass(frozen=True)
class ProviderDashboard:
    providers: ProviderCard = field(default_factory=ProviderCard)
    health: ProviderHealthCard = field(default_factory=ProviderHealthCard)
    capability: CapabilityCard3 = field(default_factory=CapabilityCard3)
    routing: RoutingCard = field(default_factory=RoutingCard)
    preview: PreviewCard3 = field(default_factory=PreviewCard3)
    statistics: StatisticsCard3 = field(default_factory=StatisticsCard3)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ProviderDashboardBuilder:
    @staticmethod
    def build(registry: ProviderRegistry, routing_summary=None, last_preview=None):
        s = registry.get_statistics()
        pc = ProviderCard(total=s.total,healthy=s.healthy,unhealthy=s.unhealthy,by_type=s.by_type)
        hc = ProviderHealthCard(overall_healthy=s.unhealthy==0,total=s.total,healthy=s.healthy,unhealthy=s.unhealthy)
        entries = registry.list()
        types = tuple(e.provider_type for e in entries)
        total_caps = sum(len(e.capability_names) for e in entries)
        cc = CapabilityCard3(total_types=len(set(types)),total_capabilities=total_caps,types=types)
        if routing_summary:
            sr = routing_summary.successful/max(routing_summary.total_decisions,1)
            rc = RoutingCard(total_decisions=routing_summary.total_decisions,success_rate=round(sr,4),
                provider_types=routing_summary.provider_types)
        else: rc = RoutingCard()
        if last_preview:
            pvc = PreviewCard3(last_preview=last_preview.preview[:100],success=last_preview.success,
                provider_type=last_preview.provider_type)
        else: pvc = PreviewCard3()
        stc = StatisticsCard3(total_providers=s.total,total_capabilities=total_caps,
            avg_health=round(s.healthy/max(s.total,1),4))
        return ProviderDashboard(providers=pc,health=hc,capability=cc,routing=rc,preview=pvc,statistics=stc)
