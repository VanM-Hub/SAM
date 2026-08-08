"""Platform Health Intelligence - Workstream C9.

Observability Platform secara keseluruhan:
- C9.1 PlatformHealthReport (unified health seluruh platform)
- C9.2 PlatformMetrics (metrik agregat platform)
- C9.3 Cross-Runtime Health (korelasi health antar runtime)
- C9.4 Platform Status Summary (ringkasan status platform)

READ-ONLY. Health DIHITUNG dari publikasi yang tersedia (bukan dipaksa).
TIDAK mengubah Runtime, TIDAK mengubah Readiness, TIDAK menambah runtime.
Mengagregasi observasi yang sudah ada (C6/C8 + PublicationRegistry).
Sesuai constraint AP-2C-001 & Directive EA-C05 (C9): observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C9.1 Platform Health Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PlatformHealthReport:
    """Unified health platform (immutable, read-only)."""
    overall_health: str = "unknown"  # healthy | degraded | unhealthy | unknown
    total_runtimes: int = 0
    healthy_runtimes: int = 0
    degraded_runtimes: int = 0
    critical_runtimes: int = 0
    healthy_ratio: float = 0.0  # 0.0 .. 1.0

    def as_dict(self) -> dict:
        return {
            "overall_health": self.overall_health,
            "total_runtimes": self.total_runtimes,
            "healthy_runtimes": self.healthy_runtimes,
            "degraded_runtimes": self.degraded_runtimes,
            "critical_runtimes": self.critical_runtimes,
            "healthy_ratio": round(self.healthy_ratio, 3),
        }


# ═══════════════════════════════════════════════════════════════════════
# C9.2 Platform Metrics
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PlatformMetrics:
    """Metrik agregat seluruh platform (immutable)."""
    total_runtimes: int = 0
    operational_runtimes: int = 0
    total_metrics: int = 0
    total_health_checks: int = 0
    total_timeline_events: int = 0

    def as_dict(self) -> dict:
        return {
            "total_runtimes": self.total_runtimes,
            "operational_runtimes": self.operational_runtimes,
            "total_metrics": self.total_metrics,
            "total_health_checks": self.total_health_checks,
            "total_timeline_events": self.total_timeline_events,
        }


# ═══════════════════════════════════════════════════════════════════════
# C9.3 Cross-Runtime Health
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CrossRuntimeHealth:
    """Korelasi health lintas runtime (immutable)."""
    runtime_id: str = ""
    health_state: str = "unknown"
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    dependency_health: str = "unknown"  # sehat jika seluruh dependensi healthy

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "health_state": self.health_state,
            "depends_on": list(self.depends_on),
            "dependency_health": self.dependency_health,
        }


@dataclass(frozen=True)
class CrossRuntimeHealthView:
    """Korelasi health lintas runtime seluruh platform (immutable)."""
    entries: Tuple[CrossRuntimeHealth, ...] = field(default_factory=tuple)

    def dependency_issues(self) -> Tuple[CrossRuntimeHealth, ...]:
        """Runtime yang sehat tapi punya dependensi tidak sehat."""
        return tuple(e for e in self.entries
                     if e.health_state == "healthy" and e.dependency_health == "degraded")

    def as_dict(self) -> dict:
        return {"cross_runtime": [e.as_dict() for e in self.entries]}


# ═══════════════════════════════════════════════════════════════════════
# C9.4 Platform Status Summary
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PlatformStatusSummary:
    """Ringkasan status platform (immutable)."""
    health: str = "unknown"
    readiness: str = "unknown"
    operational_count: int = 0
    total_runtimes: int = 0
    summary_text: str = ""

    def as_dict(self) -> dict:
        return {
            "health": self.health,
            "readiness": self.readiness,
            "operational_count": self.operational_count,
            "total_runtimes": self.total_runtimes,
            "summary_text": self.summary_text,
        }


# ═══════════════════════════════════════════════════════════════════════
# C9 Observer
# ═══════════════════════════════════════════════════════════════════════

# Dependency antar runtime (statis metadata, sama dengan C8)
_DEPENDENCIES: dict = {
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


class PlatformHealthObserver:
    """Observer Platform - health & status platform (read-only).

    Health DIHITUNG dari publikasi yang sudah tersedia (bukan dipaksa).
    Tidak mengubah runtime/readiness. Mengagregasi observasi C6/C8.
    """

    def __init__(self, registry=None, runtime_observer=None, capability_observer=None) -> None:
        """registry = PublicationRegistry; observer runtime/capability optional (seeded)."""
        self._registry = registry
        self._runtime_observer = runtime_observer
        self._capability_observer = capability_observer

    # ── observers / registries ──
    def _get_runtime_observer(self):
        if self._runtime_observer is not None:
            return self._runtime_observer
        try:
            from sam.runtime_service.api.observation_wiring import get_runtime_intelligence_observer
            return get_runtime_intelligence_observer()
        except Exception:
            return None

    def _get_registry(self):
        if self._registry is not None:
            return self._registry
        try:
            from sam.runtime_service.api.observation_wiring import get_publication_registry
            return get_publication_registry()
        except Exception:
            return None

    def _publications(self) -> Tuple:
        reg = self._get_registry()
        if reg is None:
            return ()
        try:
            return reg.observe_all().publications
        except Exception:
            return ()

    def _runtime_ids(self) -> Tuple[str, ...]:
        reg = self._get_registry()
        try:
            return tuple(sorted(reg.registered_runtimes())) if reg else ()
        except Exception:
            return tuple(sorted(p.runtime_id for p in self._publications()))

    # C9.1
    def health_report(self) -> PlatformHealthReport:
        """Unified health platform (dihitung, bukan dipaksa) (read-only)."""
        pubs = self._publications()
        if not pubs:
            # fallback statis bila registry kosong
            return PlatformHealthReport(overall_health="unknown", total_runtimes=0,
                                        healthy_runtimes=0, degraded_runtimes=0,
                                        critical_runtimes=0, healthy_ratio=0.0)
        healthy = degraded = critical = 0
        for p in pubs:
            s = p.health_state
            if s == "healthy":
                healthy += 1
            elif s == "degraded":
                degraded += 1
            elif s in ("critical", "unhealthy"):
                critical += 1
        total = len(pubs)
        ratio = (healthy / total) if total else 0.0
        if critical > 0:
            overall = "unhealthy"
        elif degraded > 0:
            overall = "degraded"
        elif healthy == total:
            overall = "healthy"
        else:
            overall = "unknown"
        return PlatformHealthReport(
            overall_health=overall, total_runtimes=total,
            healthy_runtimes=healthy, degraded_runtimes=degraded,
            critical_runtimes=critical, healthy_ratio=ratio,
        )

    # C9.2
    def metrics(self) -> PlatformMetrics:
        """Metrik agregat seluruh platform (read-only)."""
        pubs = self._publications()
        total_metrics = sum(p.metric_count or 0 for p in pubs)
        total_checks = sum(p.health_check_count or 0 for p in pubs)
        total_timeline = sum(p.timeline_events or 0 for p in pubs)
        operational = sum(1 for p in pubs if p.operational_state in ("running", "ready", "operational"))
        return PlatformMetrics(
            total_runtimes=len(pubs), operational_runtimes=operational,
            total_metrics=total_metrics, total_health_checks=total_checks,
            total_timeline_events=total_timeline,
        )

    # C9.3
    def cross_runtime_health(self) -> CrossRuntimeHealthView:
        """Korelasi health lintas runtime (read-only)."""
        pubs = self._publications()
        by_id = {p.runtime_id: p for p in pubs}
        entries: List[CrossRuntimeHealth] = []
        for rid in self._runtime_ids():
            state = by_id[rid].health_state if rid in by_id else "unknown"
            deps = tuple(_DEPENDENCIES.get(rid, ()))
            dep_states = [by_id[d].health_state for d in deps if d in by_id]
            if dep_states and any(s in ("critical", "unhealthy") for s in dep_states):
                dep_health = "degraded"
            elif dep_states and any(s != "healthy" for s in dep_states):
                dep_health = "degraded"
            elif dep_states:
                dep_health = "healthy"
            else:
                dep_health = "unknown"
            entries.append(CrossRuntimeHealth(runtime_id=rid, health_state=state,
                                              depends_on=deps, dependency_health=dep_health))
        return CrossRuntimeHealthView(entries=tuple(entries))

    # C9.4
    def status_summary(self) -> PlatformStatusSummary:
        """Ringkasan status platform (read-only)."""
        hl = self.health_report()
        pubs = self._publications()
        readinesses = {p.readiness_level for p in pubs if p.readiness_level}
        readiness = "operational" if readinesses <= {"operational"} and readinesses else \
                    ("mixed" if readinesses else "unknown")
        operational = sum(1 for p in pubs if p.readiness_level == "operational")
        text = {
            "healthy": "Platform sehat: seluruh runtime operational.",
            "degraded": "Platform degraded: sebagian runtime memerlukan perhatian.",
            "unhealthy": "Platform unhealthy: ada runtime critical.",
        }.get(hl.overall_health, "Status platform belum dapat ditentukan.")
        return PlatformStatusSummary(
            health=hl.overall_health, readiness=readiness,
            operational_count=operational, total_runtimes=hl.total_runtimes,
            summary_text=text,
        )

    # ── C9 Observer utama ──
    def observe(self) -> tuple:
        """Agregasi seluruh observasi platform (read-only).

        Returns tuple (health_report, metrics, cross_runtime_health, status_summary).
        """
        return (self.health_report(), self.metrics(), self.cross_runtime_health(), self.status_summary())
