"""Runtime Publication Adapter & Registry — WP-C1.1.

Observation Layer: membaca data yang sudah dipublikasikan oleh runtime resmi.
Pure read-only. Tidak ada mutation, tidak ada execution, tidak ada governance.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple


# ── Publication DTOs (immutable, read-only) ──

@dataclass(frozen=True)
class RuntimePublication:
    """Snapshot publikasi satu runtime (immutable, read-only snapshot)."""
    runtime_id: str
    health_state: str = "unknown"       # healthy | degraded | unhealthy | unknown
    readiness_level: str = "unknown"    # operational | activated | planned | unknown
    operational_state: str = "unknown"  # running | degraded | stopped | unknown
    metric_count: int = 0
    dashboard_count: int = 0
    health_check_count: int = 0
    snapshot_count: int = 0
    timeline_events: int = 0
    has_preview: bool = False
    has_metadata: bool = False
    has_lifecycle: bool = False
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "health_state": self.health_state,
            "readiness_level": self.readiness_level,
            "operational_state": self.operational_state,
            "metric_count": self.metric_count,
            "dashboard_count": self.dashboard_count,
            "health_check_count": self.health_check_count,
            "snapshot_count": self.snapshot_count,
            "timeline_events": self.timeline_events,
            "has_preview": self.has_preview,
            "has_metadata": self.has_metadata,
            "has_lifecycle": self.has_lifecycle,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ObservationReport:
    """Laporan observasi seluruh runtime (immutable aggregate)."""
    runtime_count: int
    publications: Tuple[RuntimePublication, ...]
    aggregated_health: str = "unknown"
    timestamp: str = ""

    def as_dict(self) -> dict:
        return {
            "runtime_count": self.runtime_count,
            "aggregated_health": self.aggregated_health,
            "timestamp": self.timestamp,
            "publications": [p.as_dict() for p in self.publications],
        }


# ── Publication Adapter (base, read-only) ──

class PublicationAdapter(ABC):
    """Base adapter untuk membaca publikasi runtime.

    READ-ONLY. Tidak boleh:
    - Memanggil execute/approve/mutate
    - Menambah runtime state
    - Menambah business logic
    """

    @abstractmethod
    def runtime_id(self) -> str:
        """ID runtime yang diobservasi."""
        ...

    @abstractmethod
    def observe(self) -> RuntimePublication:
        """Membaca publikasi runtime saat ini — pure read-only snapshot."""
        ...

    def health_state(self) -> str:
        """Shortcut: baca health state dari runtime."""
        return self.observe().health_state


# ── Publication Registry ──

class PublicationRegistry:
    """Registry adapter publikasi runtime (read-only).

    Mendaftarkan semua PublicationAdapter dan menyediakan aggregate view.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, PublicationAdapter] = {}

    def register(self, adapter: PublicationAdapter) -> None:
        self._adapters[adapter.runtime_id()] = adapter

    def registered_runtimes(self) -> FrozenSet[str]:
        return frozenset(self._adapters.keys())

    def observe(self, runtime_id: str) -> Optional[RuntimePublication]:
        adapter = self._adapters.get(runtime_id)
        if adapter is None:
            return None
        return adapter.observe()

    def observe_all(self) -> ObservationReport:
        publications: List[RuntimePublication] = []
        for adapter in self._adapters.values():
            publications.append(adapter.observe())

        # Aggregate health
        states = {p.health_state for p in publications}
        if "unhealthy" in states:
            aggregated = "unhealthy"
        elif "degraded" in states:
            aggregated = "degraded"
        elif all(s == "healthy" for s in states):
            aggregated = "healthy"
        else:
            aggregated = "unknown"

        return ObservationReport(
            runtime_count=len(publications),
            publications=tuple(publications),
            aggregated_health=aggregated,
        )
