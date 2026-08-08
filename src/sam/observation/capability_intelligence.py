"""Capability Operational Intelligence - Workstream C6.

Observability mendalam terhadap seluruh capability platform:
- C6.1 Capability Status Aggregation (status tiap capability per runtime)
- C6.2 Capability Readiness Report (readiness per capability)
- C6.3 Capability Health Report (health per capability)
- C6.4 Capability Dependency View (ketergantungan antar capability)

READ-ONLY. Observer HANYA membaca Publication Registry, Observation Report,
Capability Metadata, Readiness Report. TIDAK membaca internal Runtime Engine.
Tidak mengubah runtime, tidak mengubah readiness, tidak membuat capability baru.
Sesuai constraint AP-2C-001 & Directive EA-C05: observe, never govern.

Source data:
- CapabilityStatusReader (observation/capability.py, WP-C1.4) - status statis metadata
- PublicationRegistry (observation/publication.py) - publikasi live runtime
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C6.1 Capability Status Aggregation
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CapabilityStatusEntry:
    """Status satu capability per runtime (immutable, read-only)."""
    runtime_id: str = ""
    capability: str = ""
    available: bool = False

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "capability": self.capability,
            "available": self.available,
        }


@dataclass(frozen=True)
class CapabilityAggregation:
    """Agregasi status seluruh capability (immutable)."""
    entries: Tuple[CapabilityStatusEntry, ...] = field(default_factory=tuple)
    total_capabilities: int = 0
    available_count: int = 0

    @property
    def unavailable_count(self) -> int:
        return self.total_capabilities - self.available_count

    def by_runtime(self, runtime_id: str) -> Tuple[CapabilityStatusEntry, ...]:
        return tuple(e for e in self.entries if e.runtime_id == runtime_id)

    def as_dict(self) -> dict:
        return {
            "total_capabilities": self.total_capabilities,
            "available_count": self.available_count,
            "unavailable_count": self.unavailable_count,
            "capabilities": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C6.2 Capability Readiness Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CapabilityReadinessEntry:
    """Readiness satu capability per runtime (immutable)."""
    runtime_id: str = ""
    readiness: str = "unknown"  # operational | activated | planned | unknown
    operational: str = "unknown"  # running | degraded | stopped | unknown

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "readiness": self.readiness,
            "operational": self.operational,
        }


@dataclass(frozen=True)
class CapabilityReadinessReport:
    """Laporan readiness seluruh capability (immutable)."""
    entries: Tuple[CapabilityReadinessEntry, ...] = field(default_factory=tuple)
    operational_count: int = 0
    activated_count: int = 0
    planned_count: int = 0

    def as_dict(self) -> dict:
        return {
            "operational_count": self.operational_count,
            "activated_count": self.activated_count,
            "planned_count": self.planned_count,
            "capabilities": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C6.3 Capability Health Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CapabilityHealthEntry:
    """Health satu capability per runtime (immutable)."""
    runtime_id: str = ""
    health_state: str = "unknown"  # healthy | degraded | critical | unknown
    healthy: bool = False
    degraded: bool = False
    critical: bool = False

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "health_state": self.health_state,
            "healthy": self.healthy,
            "degraded": self.degraded,
            "critical": self.critical,
        }


@dataclass(frozen=True)
class CapabilityHealthReport:
    """Laporan health seluruh capability (immutable)."""
    entries: Tuple[CapabilityHealthEntry, ...] = field(default_factory=tuple)
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
            "capabilities": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C6.4 Capability Dependency View
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CapabilityDependency:
    """Ketergantungan satu runtime ke capability lain (immutable)."""
    runtime_id: str = ""
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True)
class CapabilityDependencyView:
    """Graf ketergantungan capability seluruh runtime (immutable)."""
    dependencies: Tuple[CapabilityDependency, ...] = field(default_factory=tuple)

    def dependencies_of(self, runtime_id: str) -> Tuple[str, ...]:
        for d in self.dependencies:
            if d.runtime_id == runtime_id:
                return d.depends_on
        return ()

    def as_dict(self) -> dict:
        return {"dependencies": [d.as_dict() for d in self.dependencies]}


# ═══════════════════════════════════════════════════════════════════════
# C6 Observer
# ═══════════════════════════════════════════════════════════════════════

# Dependency antar runtime (statis, berbasis metadata - bukan runtime engine)
_CAPABILITY_DEPENDENCIES: dict = {
    "mission": (),
    "workflow": ("mission",),
    "policy": ("mission",),
    "execution": ("mission", "workflow", "policy"),
    "approval": ("workflow",),
    "audit": ("mission", "workflow", "execution"),
    "knowledge": (),
    "memory": ("knowledge",),
    "artifact": ("knowledge",),
    "runtime_service": ("mission", "knowledge", "memory"),
}


class CapabilityIntelligenceObserver:
    """Observer Capability - membaca publikasi capability (read-only).

    Sumber data (sesuai Directive C6):
    - Capability Metadata (melalui CapabilityStatusReader di observation/capability.py)
    - Publication Registry (publikasi live runtime)
    - Readiness Report (dari CapabilityStatusReader)
    Dibangun di atas fondasi WP-C1.4; TIDAK dari nol (verify, don't build).
    Tidak membaca internal Runtime Engine.
    """

    def __init__(self, registry=None) -> None:
        """registry = PublicationRegistry (opsional untuk fallback observasi live)."""
        self._registry = registry

    # ── Capability Status Reader (fondasi WP-C1.4) ──
    def _status_reader(self):
        try:
            from sam.observation.capability import CapabilityStatusReader
            return CapabilityStatusReader()
        except Exception:
            return None

    def _runtime_list(self) -> Tuple[str, ...]:
        reader = self._status_reader()
        if reader is not None:
            return tuple(sorted(reader._RUNTIME_CAPABILITIES.keys()))
        if self._registry is not None:
            try:
                return tuple(sorted(p.runtime_id for p in self._registry.observe_all().publications))
            except Exception:
                return ()
        return ()

    # C6.1
    def aggregation(self) -> CapabilityAggregation:
        """Agregasi status seluruh capability (read-only)."""
        reader = self._status_reader()
        entries: List[CapabilityStatusEntry] = []
        known = self._runtime_list()

        if reader is not None:
            try:
                matrix = reader.read_all()
                cap_names = ("dashboard", "health", "metrics", "preview", "timeline", "lifecycle", "metadata", "snapshot")
                for st in matrix.statuses:
                    for cap in cap_names:
                        has = getattr(st, "has_" + cap, False)
                        entries.append(CapabilityStatusEntry(
                            runtime_id=st.runtime_id,
                            capability=cap,
                            available=bool(has),
                        ))
                return CapabilityAggregation(
                    entries=tuple(entries),
                    total_capabilities=len(entries),
                    available_count=sum(1 for e in entries if e.available),
                )
            except Exception:
                pass

        # Fallback: registry live
        for rt in known:
            pub = self._publication_for(rt)
            if pub is None:
                continue
            for cap in ("dashboard", "health", "metrics", "preview", "timeline", "lifecycle", "metadata", "snapshot"):
                has = getattr(pub, "has_" + cap, False)
                entries.append(CapabilityStatusEntry(
                    runtime_id=rt, capability=cap, available=bool(has),
                ))
        return CapabilityAggregation(
            entries=tuple(entries),
            total_capabilities=len(entries),
            available_count=sum(1 for e in entries if e.available),
        )

    # C6.2
    def readiness(self) -> CapabilityReadinessReport:
        """Laporan readiness per capability (read-only)."""
        reader = self._status_reader()
        entries: List[CapabilityReadinessEntry] = []
        op = ac = pl = 0

        if reader is not None:
            try:
                matrix = reader.read_all()
                for st in matrix.statuses:
                    readiness = st.readiness
                    operational = st.operational
                    if readiness == "operational":
                        op += 1
                    elif readiness == "activated":
                        ac += 1
                    else:
                        pl += 1
                    entries.append(CapabilityReadinessEntry(
                        runtime_id=st.runtime_id, readiness=readiness, operational=operational,
                    ))
                return CapabilityReadinessReport(
                    entries=tuple(entries), operational_count=op, activated_count=ac, planned_count=pl,
                )
            except Exception:
                pass

        for rt in self._runtime_list():
            pub = self._publication_for(rt)
            readiness = pub.readiness if pub else "unknown"
            operational = pub.operational_state if pub else "unknown"
            if readiness == "operational":
                op += 1
            elif readiness == "activated":
                ac += 1
            else:
                pl += 1
            entries.append(CapabilityReadinessEntry(runtime_id=rt, readiness=readiness, operational=operational))
        return CapabilityReadinessReport(
            entries=tuple(entries), operational_count=op, activated_count=ac, planned_count=pl,
        )

    # C6.3
    def health(self) -> CapabilityHealthReport:
        """Laporan health per capability (read-only)."""
        reader = self._status_reader()
        entries: List[CapabilityHealthEntry] = []
        healthy = degraded = critical = 0

        for rt in self._runtime_list():
            state = "unknown"
            pub = self._publication_for(rt)
            if pub is not None:
                state = pub.health_state or "unknown"
            if state == "healthy":
                healthy += 1
            elif state == "degraded":
                degraded += 1
            elif state == "critical":
                critical += 1
            entries.append(CapabilityHealthEntry(
                runtime_id=rt,
                health_state=state,
                healthy=state == "healthy",
                degraded=state == "degraded",
                critical=state == "critical",
            ))

        if not entries and reader is not None:
            # fallback statis bila registry kosong: sehat (metadata menunjukkan ada health capability)
            try:
                matrix = reader.read_all()
                for st in matrix.statuses:
                    state = "healthy" if st.has_health else "unknown"
                    if state == "healthy":
                        healthy += 1
                    entries.append(CapabilityHealthEntry(runtime_id=st.runtime_id, health_state=state,
                                                         healthy=state == "healthy", degraded=False, critical=False))
            except Exception:
                pass

        return CapabilityHealthReport(
            entries=tuple(entries), healthy_count=healthy, degraded_count=degraded, critical_count=critical,
        )

    # C6.4
    def dependency_view(self) -> CapabilityDependencyView:
        """Graf ketergantungan capability (read-only, dari metadata statis)."""
        deps: List[CapabilityDependency] = []
        for rt in self._runtime_list():
            deps.append(CapabilityDependency(
                runtime_id=rt,
                depends_on=tuple(_CAPABILITY_DEPENDENCIES.get(rt, ())),
            ))
        return CapabilityDependencyView(dependencies=tuple(deps))

    # ── C6 Observer utama ──
    def observe(self) -> tuple:
        """Agregasi seluruh observasi capability (read-only).

        Returns tuple (aggregation, readiness, health, dependency_view).
        """
        return (self.aggregation(), self.readiness(), self.health(), self.dependency_view())

    # ── helper ──
    def _publication_for(self, runtime_id: str):
        if self._registry is None:
            return None
        try:
            for pub in self._registry.observe_all().publications:
                if pub.runtime_id == runtime_id:
                    return pub
        except Exception:
            return None
        return None
