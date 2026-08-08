"""Runtime Operational Intelligence - Workstream C8.

Observability mendalam terhadap seluruh Runtime (agregasi lintas runtime):
- C8.1 Runtime Status Matrix (status operational tiap runtime)
- C8.2 Runtime Dependency View (ketergantungan antar runtime)
- C8.3 Runtime Lifecycle View (lifecycle capability per runtime)
- C8.4 Runtime Health Matrix (health state tiap runtime + agregat)

READ-ONLY. Observer HANYA membaca Publication Registry (agregasi publikasi
runtime yang sudah tersedia). TIDAK mengubah lifecycle Runtime, TIDAK publish
Runtime state baru, HANYA mengagregasi publication yang sudah ada.
Sesuai constraint AP-2C-001 & Directive EA-C05 (C8): observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C8.1 Runtime Status Matrix
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RuntimeStatusEntry:
    """Status satu runtime (immutable, read-only)."""
    runtime_id: str = ""
    operational_state: str = "unknown"  # running | ready | degraded | stopped | unknown
    readiness_level: str = "unknown"    # operational | activated | planned
    metric_count: int = 0

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "operational_state": self.operational_state,
            "readiness_level": self.readiness_level,
            "metric_count": self.metric_count,
        }


@dataclass(frozen=True)
class RuntimeStatusMatrix:
    """Matriks status seluruh runtime (immutable)."""
    entries: Tuple[RuntimeStatusEntry, ...] = field(default_factory=tuple)
    total_runtimes: int = 0
    operational_count: int = 0
    degraded_count: int = 0
    ready_count: int = 0

    def as_dict(self) -> dict:
        return {
            "total_runtimes": self.total_runtimes,
            "operational_count": self.operational_count,
            "degraded_count": self.degraded_count,
            "ready_count": self.ready_count,
            "runtimes": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C8.2 Runtime Dependency View
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RuntimeDependency:
    """Ketergantungan satu runtime ke runtime lain (immutable)."""
    runtime_id: str = ""
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"runtime_id": self.runtime_id, "depends_on": list(self.depends_on)}


@dataclass(frozen=True)
class RuntimeDependencyView:
    """Graf ketergantungan seluruh runtime (immutable)."""
    dependencies: Tuple[RuntimeDependency, ...] = field(default_factory=tuple)

    def dependencies_of(self, runtime_id: str) -> Tuple[str, ...]:
        for d in self.dependencies:
            if d.runtime_id == runtime_id:
                return d.depends_on
        return ()

    def as_dict(self) -> dict:
        return {"dependencies": [d.as_dict() for d in self.dependencies]}


# ═══════════════════════════════════════════════════════════════════════
# C8.3 Runtime Lifecycle View
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RuntimeLifecycleEntry:
    """Keberadaan lifecycle capability satu runtime (immutable)."""
    runtime_id: str = ""
    has_lifecycle: bool = False
    has_timeline: bool = False
    has_metadata: bool = False

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "has_lifecycle": self.has_lifecycle,
            "has_timeline": self.has_timeline,
            "has_metadata": self.has_metadata,
        }


@dataclass(frozen=True)
class RuntimeLifecycleView:
    """View lifecycle capability seluruh runtime (immutable)."""
    entries: Tuple[RuntimeLifecycleEntry, ...] = field(default_factory=tuple)
    lifecycle_capable_count: int = 0

    def as_dict(self) -> dict:
        return {
            "lifecycle_capable_count": self.lifecycle_capable_count,
            "runtimes": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C8.4 Runtime Health Matrix
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RuntimeHealthEntry:
    """Health satu runtime (immutable)."""
    runtime_id: str = ""
    health_state: str = "unknown"  # healthy | degraded | critical | unhealthy | unknown
    healthy: bool = False
    health_check_count: int = 0

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "health_state": self.health_state,
            "healthy": self.healthy,
            "health_check_count": self.health_check_count,
        }


@dataclass(frozen=True)
class RuntimeHealthMatrix:
    """Matriks health seluruh runtime (immutable)."""
    entries: Tuple[RuntimeHealthEntry, ...] = field(default_factory=tuple)
    healthy_count: int = 0
    degraded_count: int = 0
    critical_count: int = 0
    aggregated_health: str = "unknown"

    @property
    def unhealthy_count(self) -> int:
        return self.degraded_count + self.critical_count

    def as_dict(self) -> dict:
        return {
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "critical_count": self.critical_count,
            "unhealthy_count": self.unhealthy_count,
            "aggregated_health": self.aggregated_health,
            "runtimes": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C8 Observer
# ═══════════════════════════════════════════════════════════════════════

# Dependency antar runtime (statis, metadata - bukan runtime engine)
_RUNTIME_DEPENDENCIES: dict = {
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


class RuntimeIntelligenceObserver:
    """Observer Runtime - mengagregasi publikasi seluruh runtime (read-only).

    Sumber data: PublicationRegistry (agregasi publication runtime yang sudah
    tersedia). Tidak mengubah lifecycle, tidak publish state baru, hanya agregasi.
    """

    def __init__(self, registry) -> None:
        """registry = PublicationRegistry (aggregate view publikasi runtime)."""
        self._registry = registry

    def _publications(self) -> Tuple:
        if self._registry is None:
            return ()
        try:
            return self._registry.observe_all().publications
        except Exception:
            return ()

    def _runtime_ids(self) -> Tuple[str, ...]:
        try:
            return tuple(sorted(self._registry.registered_runtimes()))
        except Exception:
            return tuple(sorted(p.runtime_id for p in self._publications()))

    # C8.1
    def status_matrix(self) -> RuntimeStatusMatrix:
        """Matriks status operational seluruh runtime (read-only)."""
        entries: List[RuntimeStatusEntry] = []
        by_id = {p.runtime_id: p for p in self._publications()}
        op = degraded = ready = 0
        for rid in self._runtime_ids():
            pub = by_id.get(rid)
            state = pub.operational_state if pub else "unknown"
            readiness = pub.readiness_level if pub else "unknown"
            metric_count = pub.metric_count if pub else 0
            if state in ("running", "ready", "operational"):
                op += 1
            if state in ("degraded", "degrading"):
                degraded += 1
            if state == "ready":
                ready += 1
            entries.append(RuntimeStatusEntry(
                runtime_id=rid, operational_state=state,
                readiness_level=readiness, metric_count=metric_count,
            ))
        return RuntimeStatusMatrix(
            entries=tuple(entries), total_runtimes=len(entries),
            operational_count=op, degraded_count=degraded, ready_count=ready,
        )

    # C8.2
    def dependency_view(self) -> RuntimeDependencyView:
        """Graf ketergantungan antar runtime (read-only, metadata statis)."""
        deps: List[RuntimeDependency] = []
        for rid in self._runtime_ids():
            deps.append(RuntimeDependency(
                runtime_id=rid,
                depends_on=tuple(_RUNTIME_DEPENDENCIES.get(rid, ())),
            ))
        return RuntimeDependencyView(dependencies=tuple(deps))

    # C8.3
    def lifecycle_view(self) -> RuntimeLifecycleView:
        """View lifecycle capability seluruh runtime (read-only)."""
        entries: List[RuntimeLifecycleEntry] = []
        by_id = {p.runtime_id: p for p in self._publications()}
        lc_count = 0
        for rid in self._runtime_ids():
            pub = by_id.get(rid)
            has_lc = bool(pub.has_lifecycle) if pub else False
            has_tl = (pub.timeline_events and pub.timeline_events > 0) if pub else False
            has_md = bool(pub.has_metadata) if pub else False
            if has_lc:
                lc_count += 1
            entries.append(RuntimeLifecycleEntry(
                runtime_id=rid, has_lifecycle=has_lc,
                has_timeline=has_tl, has_metadata=has_md,
            ))
        return RuntimeLifecycleView(entries=tuple(entries), lifecycle_capable_count=lc_count)

    # C8.4
    def health_matrix(self) -> RuntimeHealthMatrix:
        """Matriks health seluruh runtime (read-only)."""
        entries: List[RuntimeHealthEntry] = []
        by_id = {p.runtime_id: p for p in self._publications()}
        healthy = degraded = critical = 0
        for rid in self._runtime_ids():
            pub = by_id.get(rid)
            state = pub.health_state if pub else "unknown"
            check_count = pub.health_check_count if pub else 0
            if state == "healthy":
                healthy += 1
            elif state == "degraded":
                degraded += 1
            elif state in ("critical", "unhealthy"):
                critical += 1
            entries.append(RuntimeHealthEntry(
                runtime_id=rid, health_state=state,
                healthy=state == "healthy", health_check_count=check_count,
            ))
        aggregated = self._aggregate(state for e in entries for state in [e.health_state])
        return RuntimeHealthMatrix(
            entries=tuple(entries), healthy_count=healthy,
            degraded_count=degraded, critical_count=critical,
            aggregated_health=aggregated,
        )

    @staticmethod
    def _aggregate(states) -> str:
        states = list(states)
        if not states:
            return "unknown"
        if "critical" in states or "unhealthy" in states:
            return "unhealthy"
        if "degraded" in states:
            return "degraded"
        if all(s == "healthy" for s in states):
            return "healthy"
        return "unknown"

    # ── C8 Observer utama ──
    def observe(self) -> tuple:
        """Agregasi seluruh observasi runtime (read-only).

        Returns tuple (status_matrix, dependency_view, lifecycle_view, health_matrix).
        """
        return (self.status_matrix(), self.dependency_view(),
                self.lifecycle_view(), self.health_matrix())
