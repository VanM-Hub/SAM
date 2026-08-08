"""Provider Operational Intelligence - Workstream C7.

Observability mendalam terhadap provider (metadata provider, BUKAN Provider Runtime):
- C7.1 Provider Availability Report (registered/discovered/total)
- C7.2 Provider Readiness Report (state readiness per provider)
- C7.3 Provider Connectivity Report (konektivitas terdaftar -> kontrak/capability)
- C7.4 Provider Health Report (health indikator dari status metadata)
- C7.5 Provider Metrics (per-type aggregation)

READ-ONLY. Observer HANYA membaca publication metadata provider yang SUDAH tersedia
(ProviderRegistry - preview-only, synchronous, deterministic, tidak panggil eksternal).
TIDAK boleh: connect provider, authenticate, retry, execute provider, mutate config.
TIDAK membaca internal Provider Runtime engine / tidak memanggil BaseProvider.
Sesuai constraint AP-2C-001 & Directive EA-C05 (C7): observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C7.1 Provider Availability Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProviderAvailability:
    """Availability satu provider (immutable, read-only)."""
    provider_id: str
    registered: bool = False
    discovered: bool = False
    state: str = "unknown"

    @property
    def available(self) -> bool:
        return self.registered

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "registered": self.registered,
            "discovered": self.discovered,
            "state": self.state,
            "available": self.available,
        }


@dataclass(frozen=True)
class ProviderAvailabilityReport:
    """Laporan availability seluruh provider (immutable)."""
    entries: Tuple[ProviderAvailability, ...] = field(default_factory=tuple)
    total_providers: int = 0
    registered_count: int = 0
    discovered_count: int = 0

    @property
    def unregistered_count(self) -> int:
        return self.total_providers - self.registered_count

    def as_dict(self) -> dict:
        return {
            "total_providers": self.total_providers,
            "registered_count": self.registered_count,
            "discovered_count": self.discovered_count,
            "unregistered_count": self.unregistered_count,
            "providers": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C7.2 Provider Readiness Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProviderReadiness:
    """Readiness satu provider (immutable)."""
    provider_id: str = ""
    state: str = "unknown"  # defined | registered | discovered | ready | unknown
    ready: bool = False

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "state": self.state,
            "ready": self.ready,
        }


@dataclass(frozen=True)
class ProviderReadinessReport:
    """Laporan readiness seluruh provider (immutable)."""
    entries: Tuple[ProviderReadiness, ...] = field(default_factory=tuple)
    ready_count: int = 0
    not_ready_count: int = 0

    def as_dict(self) -> dict:
        return {
            "ready_count": self.ready_count,
            "not_ready_count": self.not_ready_count,
            "providers": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C7.3 Provider Connectivity Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProviderConnectivity:
    """Konektivitas satu provider dari metadata (immutable)."""
    provider_id: str = ""
    has_contract: bool = False
    contract_count: int = 0
    capability_count: int = 0

    @property
    def connected(self) -> bool:
        # konektivitas metadata: ada kontrak ATAU capability terpasang
        return self.has_contract or self.capability_count > 0

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "has_contract": self.has_contract,
            "contract_count": self.contract_count,
            "capability_count": self.capability_count,
            "connected": self.connected,
        }


@dataclass(frozen=True)
class ProviderConnectivityReport:
    """Laporan konektivitas seluruh provider (immutable)."""
    entries: Tuple[ProviderConnectivity, ...] = field(default_factory=tuple)
    connected_count: int = 0

    @property
    def disconnected_count(self) -> int:
        return len(self.entries) - self.connected_count

    def as_dict(self) -> dict:
        return {
            "connected_count": self.connected_count,
            "disconnected_count": self.disconnected_count,
            "providers": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C7.4 Provider Health Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProviderHealth:
    """Health indikator satu provider, diderivasi dari status metadata (immutable).

    Health dihitung (bukan dipaksa): provider sehat bila terdaftar DAN
    ber-state ready/discovered. Degraded bila terdaftar tapi belum ready.
    """
    provider_id: str = ""
    state: str = "unknown"
    healthy: bool = False
    degraded: bool = False
    critical: bool = False

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "state": self.state,
            "healthy": self.healthy,
            "degraded": self.degraded,
            "critical": self.critical,
        }


@dataclass(frozen=True)
class ProviderHealthReport:
    """Laporan health seluruh provider (immutable)."""
    entries: Tuple[ProviderHealth, ...] = field(default_factory=tuple)
    healthy_count: int = 0
    degraded_count: int = 0
    critical_count: int = 0

    @property
    def unhealthy_count(self) -> int:
        return self.degraded_count + self.critical_count

    def as_dict(self) -> dict:
        return {
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "critical_count": self.critical_count,
            "unhealthy_count": self.unhealthy_count,
            "providers": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C7.5 Provider Metrics
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ProviderTypeMetric:
    """Metrik agregat per tipe provider (immutable)."""
    provider_type: str = ""
    count: int = 0

    def as_dict(self) -> dict:
        return {"provider_type": self.provider_type, "count": self.count}


@dataclass(frozen=True)
class ProviderMetrics:
    """Metrik provider lintas kategori (immutable)."""
    total_providers: int = 0
    registered_providers: int = 0
    discovered_providers: int = 0
    ready_providers: int = 0
    by_type: Tuple[ProviderTypeMetric, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "total_providers": self.total_providers,
            "registered_providers": self.registered_providers,
            "discovered_providers": self.discovered_providers,
            "ready_providers": self.ready_providers,
            "by_type": [m.as_dict() for m in self.by_type],
        }


# ═══════════════════════════════════════════════════════════════════════
# C7 Observer
# ═══════════════════════════════════════════════════════════════════════

class ProviderIntelligenceObserver:
    """Observer Provider - membaca metadata provider (read-only).

    Sumber data: ProviderRegistry (preview-only, synchronous, deterministik,
    TIDAK melakukan panggilan eksternal). Membaca ProviderDescriptor,
    ProviderStatus, ProviderCapability, ProviderContract yang SUDAH terdaftar.
    TIDAK memanggil BaseProvider / tidak connect / tidak authenticate /
    tidak retry / tidak execute / tidak mutate config.
    """

    def __init__(self, registry=None) -> None:
        """registry = ProviderRegistry opsional (preview-only metadata)."""
        self._registry = registry

    def _get_registry(self):
        if self._registry is not None:
            return self._registry
        try:
            from sam.providers.registry.provider_registry import ProviderRegistry as PR
            return PR()
        except Exception:
            return None

    def _provider_ids(self) -> Tuple[str, ...]:
        reg = self._get_registry()
        if reg is None:
            return ()
        try:
            return tuple(reg.list_ids())
        except Exception:
            return ()

    # C7.1
    def availability(self) -> ProviderAvailabilityReport:
        """Laporan availability seluruh provider (read-only)."""
        reg = self._get_registry()
        entries: List[ProviderAvailability] = []
        for pid in self._provider_ids():
            st = reg.get_status(pid) if reg else None
            registered = bool(st and st.registered)
            discovered = bool(st and st.discovered)
            state = st.state if st else "unknown"
            entries.append(ProviderAvailability(provider_id=pid, registered=registered,
                                                discovered=discovered, state=state))
        return ProviderAvailabilityReport(
            entries=tuple(entries),
            total_providers=len(entries),
            registered_count=sum(1 for e in entries if e.registered),
            discovered_count=sum(1 for e in entries if e.discovered),
        )

    # C7.2
    def readiness(self) -> ProviderReadinessReport:
        """Laporan readiness seluruh provider (read-only)."""
        reg = self._get_registry()
        entries: List[ProviderReadiness] = []
        for pid in self._provider_ids():
            st = reg.get_status(pid) if reg else None
            state = st.state if st else "unknown"
            ready = state in ("ready", "discovered")
            entries.append(ProviderReadiness(provider_id=pid, state=state, ready=ready))
        return ProviderReadinessReport(
            entries=tuple(entries),
            ready_count=sum(1 for e in entries if e.ready),
            not_ready_count=sum(1 for e in entries if not e.ready),
        )

    # C7.3
    def connectivity(self) -> ProviderConnectivityReport:
        """Laporan konektivitas provider dari metadata (read-only)."""
        reg = self._get_registry()
        entries: List[ProviderConnectivity] = []
        for pid in self._provider_ids():
            caps = reg.get_capabilities(pid) if reg else []
            contract = reg.get_contract(pid) if reg else None
            cap_count = len(caps) if caps else 0
            entries.append(ProviderConnectivity(
                provider_id=pid,
                has_contract=bool(contract),
                contract_count=1 if contract else 0,
                capability_count=cap_count,
            ))
        return ProviderConnectivityReport(
            entries=tuple(entries),
            connected_count=sum(1 for e in entries if e.connected),
        )

    # C7.4
    def health(self) -> ProviderHealthReport:
        """Laporan health provider diderivasi dari status metadata (read-only)."""
        reg = self._get_registry()
        entries: List[ProviderHealth] = []
        healthy = degraded = critical = 0
        for pid in self._provider_ids():
            st = reg.get_status(pid) if reg else None
            state = st.state if st else "unknown"
            if state == "ready":
                h, d, c = True, False, False
                healthy += 1
            elif state in ("discovered", "registered"):
                h, d, c = False, True, False
                degraded += 1
            elif state in ("defined", "unknown"):
                h, d, c = False, False, True
                critical += 1
            else:
                h, d, c = False, False, True
                critical += 1
            entries.append(ProviderHealth(provider_id=pid, state=state,
                                          healthy=h, degraded=d, critical=c))
        return ProviderHealthReport(
            entries=tuple(entries), healthy_count=healthy,
            degraded_count=degraded, critical_count=critical,
        )

    # C7.5
    def metrics(self) -> ProviderMetrics:
        """Metrik provider agregat (read-only)."""
        reg = self._get_registry()
        ids = self._provider_ids()
        by_type: Dict[str, int] = {}
        ready_cnt = discovered_cnt = 0
        for pid in ids:
            desc = reg.get(pid) if reg else None
            ptype = desc.provider_type if desc else "generic"
            by_type[ptype] = by_type.get(ptype, 0) + 1
            st = reg.get_status(pid) if reg else None
            if st and st.state in ("ready", "discovered"):
                ready_cnt += 1
            if st and st.discovered:
                discovered_cnt += 1
        return ProviderMetrics(
            total_providers=len(ids),
            registered_providers=sum(1 for pid in ids if reg and (reg.get_status(pid).registered if reg.get_status(pid) else False)),
            discovered_providers=discovered_cnt,
            ready_providers=ready_cnt,
            by_type=tuple(ProviderTypeMetric(provider_type=k, count=v) for k, v in sorted(by_type.items())),
        )

    # ── C7 Observer utama ──
    def observe(self) -> tuple:
        """Agregasi seluruh observasi provider (read-only).

        Returns tuple (availability, readiness, connectivity, health, metrics).
        """
        return (self.availability(), self.readiness(), self.connectivity(), self.health(), self.metrics())
