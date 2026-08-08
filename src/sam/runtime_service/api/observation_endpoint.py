"""Observation API Endpoint — C-Phase 1 Unified Observation Gateway.

Menyediakan unified observation endpoint yang membaca dari PublicationRegistry.
READ-ONLY. Tidak ada execute, approve, mutate.

WP-C1.1: publication query
WP-C1.3: health aggregation (via existing runtime_kernel/health_aggregator)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional

from sam.observation.publication import ObservationReport, PublicationRegistry, RuntimePublication


# ── Observation DTO (immutable, read-only) ──

@dataclass(frozen=True)
class ObservationResponse:
    """Hasil observasi (immutable)."""
    status: str = "ok"
    runtime_count: int = 0
    aggregated_health: str = "unknown"
    publications: List[Dict[str, Any]] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.publications is None:
            object.__setattr__(self, "publications", [])

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "runtime_count": self.runtime_count,
            "aggregated_health": self.aggregated_health,
            "publications": self.publications,
        }


@dataclass(frozen=True)
class HealthOverviewResponse:
    """Overview kesehatan seluruh runtime (WP-C1.3)."""
    status: str = "ok"
    aggregated_health: str = "unknown"
    healthy_count: int = 0
    degraded_count: int = 0
    unhealthy_count: int = 0
    unknown_count: int = 0
    per_runtime: Dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.per_runtime is None:
            object.__setattr__(self, "per_runtime", {})

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "aggregated_health": self.aggregated_health,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unhealthy_count": self.unhealthy_count,
            "unknown_count": self.unknown_count,
            "per_runtime": self.per_runtime,
        }


# ── Observation Gateway ──

class ObservationGateway:
    """Gateway observasi — membaca publikasi dari registry (read-only).

    Tidak boleh:
    - Memanggil execute/approve/mutate
    - Mengubah runtime state
    - Menambah business logic
    """

    def __init__(self, registry: PublicationRegistry) -> None:
        self._registry = registry

    def registered_runtimes(self) -> FrozenSet[str]:
        return self._registry.registered_runtimes()

    def observe(self, runtime_id: str) -> ObservationResponse:
        pub = self._registry.observe(runtime_id)
        if pub is None:
            return ObservationResponse(
                status="not_found",
                runtime_count=0,
                aggregated_health="unknown",
                publications=[],
            )
        return ObservationResponse(
            status="ok",
            runtime_count=1,
            aggregated_health=pub.health_state,
            publications=[pub.as_dict()],
        )

    def observe_all(self) -> ObservationResponse:
        report = self._registry.observe_all()
        return ObservationResponse(
            status="ok",
            runtime_count=report.runtime_count,
            aggregated_health=report.aggregated_health,
            publications=[p.as_dict() for p in report.publications],
        )

    def health_overview(self) -> HealthOverviewResponse:
        """WP-C1.3: Health overview seluruh runtime."""
        report = self._registry.observe_all()
        per_runtime: Dict[str, str] = {}
        h, d, u, uk = 0, 0, 0, 0
        for p in report.publications:
            per_runtime[p.runtime_id] = p.health_state
            if p.health_state == "healthy":
                h += 1
            elif p.health_state == "degraded":
                d += 1
            elif p.health_state == "unhealthy":
                u += 1
            else:
                uk += 1

        return HealthOverviewResponse(
            status="ok",
            aggregated_health=report.aggregated_health,
            healthy_count=h,
            degraded_count=d,
            unhealthy_count=u,
            unknown_count=uk,
            per_runtime=per_runtime,
        )
