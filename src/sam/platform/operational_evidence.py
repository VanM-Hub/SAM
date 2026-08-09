# IP-3.6-C Operational Evidence - MISSION-3.6 (AO-ENG-001)
# WP-C1 (Production Audit Evidence) + WP-C2 (Operational Metrics)
# + WP-C3 (Runtime Evidence Consolidation) + WP-C4 (Platform Health Evidence)
# + WP-C5 (Governance Evidence Aggregation).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail MISSION-3.6: Operational Evidence CONSOLIDATES & AGGREGATES
#   evidence/metadata yang diberikan dari luar menjadi ringkasan teraudit.
#   Ia TIDAK mengubah evidence, runtime, atau health platform itu sendiri.

"""Operational Evidence (Track C).

Menghimpun & mengkonsolidasikan bukti operasional (audit, metrics, runtime,
health, governance evidence) menjadi ringkasan deterministik yang dapat
diaudit dan dipresentasikan. Menerima evidence sebagai input; mengubahnya
menjadi agregat; tidak pernah memodifikasi sumber.

Consolidation (bukan collection): platform tidak menjalankan sensor/agent.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple, Optional


# --- WP-C1 Production Audit Evidence -----------------------------------------

@dataclass(frozen=True)
class AuditEvent:
    """Satu kejadian audit yang diperoleh (input)."""

    event_id: str
    kind: str = "info"
    recorded: bool = False


@dataclass(frozen=True)
class AuditEvidenceSummary:
    """Ringkasan bukti audit (read-only)."""

    recorded_events: int = 0
    missing_events: int = 0
    kind_counts: Tuple[Tuple[str, int], ...] = ()

    @property
    def total(self) -> int:
        return self.recorded_events + self.missing_events


def summarize_audit_evidence(
    events: Sequence[AuditEvent],
) -> AuditEvidenceSummary:
    """Ringkas bukti audit; hitung recorded/missing dan per-kind."""
    recorded = sum(1 for e in events if e.recorded)
    missing = len(events) - recorded
    counts: dict = {}
    for e in events:
        if e.recorded:
            counts[e.kind] = counts.get(e.kind, 0) + 1
    kind_counts = tuple(sorted(counts.items()))
    return AuditEvidenceSummary(
        recorded_events=recorded,
        missing_events=missing,
        kind_counts=kind_counts,
    )


# --- WP-C2 Operational Metrics -----------------------------------------------

@dataclass(frozen=True)
class MetricPoint:
    """Satu titik metrik operasional (input)."""

    name: str
    value: float = 0.0


@dataclass(frozen=True)
class MetricsSummary:
    """Ringkasan metrik (deterministik, read-only)."""

    by_name: Tuple[Tuple[str, float], ...] = ()
    average: float = 0.0

    def value_of(self, name: str) -> Optional[float]:
        for n, v in self.by_name:
            if n == name:
                return v
        return None


def summarize_metrics(
    points: Sequence[MetricPoint],
) -> MetricsSummary:
    """Sederhanakan metrik menjadi rata-rata per nama (deterministik)."""
    sums: dict = {}
    counts: dict = {}
    for p in points:
        sums[p.name] = sums.get(p.name, 0.0) + float(p.value)
        counts[p.name] = counts.get(p.name, 0) + 1
    by_name = tuple(
        sorted((n, round(sums[n] / counts[n], 4)) for n in sums)
    )
    avg = 0.0
    if points:
        avg = round(sum(float(p.value) for p in points) / len(points), 4)
    return MetricsSummary(by_name=by_name, average=avg)


# --- WP-C3 Runtime Evidence Consolidation ------------------------------------

@dataclass(frozen=True)
class RuntimeEvidencePiece:
    """Satu potongan evidence runtime (input)."""

    source: str
    status: str = "unknown"


@dataclass(frozen=True)
class RuntimeConsolidation:
    """Konsolidasi evidence runtime (read-only)."""

    source_count: int = 0
    status_distribution: Tuple[Tuple[str, int], ...] = ()
    healthy: bool = True


def consolidate_runtime_evidence(
    pieces: Sequence[RuntimeEvidencePiece],
) -> RuntimeConsolidation:
    """Konsolidasi evidence runtime; hitung distribusi status."""
    dist: dict = {}
    for p in pieces:
        dist[p.status] = dist.get(p.status, 0) + 1
    distribution = tuple(sorted(dist.items()))
    healthy = all(p.status == "ok" for p in pieces)
    return RuntimeConsolidation(
        source_count=len(pieces),
        status_distribution=distribution,
        healthy=healthy,
    )


# --- WP-C4 Platform Health Evidence ------------------------------------------

@dataclass(frozen=True)
class HealthSignal:
    """Satu sinyal kesehatan platform (input)."""

    signal_id: str
    healthy: bool = False


@dataclass(frozen=True)
class HealthEvidenceSummary:
    """Ringkasan kesehatan platform (read-only)."""

    healthy: Tuple[str, ...] = ()
    unhealthy: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.unhealthy == ()


def summarize_health_evidence(
    signals: Sequence[HealthSignal],
) -> HealthEvidenceSummary:
    """Pisahkan sinyal sehat vs tidak sehat (deterministik)."""
    healthy = tuple(s.signal_id for s in signals if s.healthy)
    unhealthy = tuple(s.signal_id for s in signals if not s.healthy)
    return HealthEvidenceSummary(healthy=healthy, unhealthy=unhealthy)


# --- WP-C5 Governance Evidence Aggregation -----------------------------------

@dataclass(frozen=True)
class GovernanceEvidencePoint:
    """Satu poin evidence governance (input)."""

    area: str
    weight: float = 0.0


@dataclass(frozen=True)
class GovernanceEvidenceAggregate:
    """Agregat evidence governance (read-only)."""

    weighted_sum: float = 0.0
    total_weight: float = 0.0

    @property
    def normalized(self) -> float:
        return (round(self.weighted_sum / self.total_weight, 4)
                if self.total_weight else 0.0)


def aggregate_governance_evidence(
    points: Sequence[GovernanceEvidencePoint],
) -> GovernanceEvidenceAggregate:
    """Agregasi evidence governance (rata-rata tertimbang, deterministik)."""
    weighted = sum(float(p.weight) * float(p.weight) for p in points)
    total = sum(float(p.weight) for p in points)
    return GovernanceEvidenceAggregate(weighted_sum=weighted, total_weight=total)
