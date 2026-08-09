"""Runtime Observation - WP-04 (MISSION-4.2 / IP-4.2-001).

Mengamati kondisi Runtime secara read-only. Runtime diamati tanpa mutation,
snapshot immutable, observation dapat dijelaskan, menghasilkan evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .evidence_collection import EvidenceModel, EvidenceSource


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Snapshot kondisi runtime (immutable)."""

    captured_at: str
    runtime_id: str
    status: str
    metrics: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)
    health: str = "unknown"
    snapshot_hash: str = ""

    def as_dict(self) -> dict:
        return {
            "captured_at": self.captured_at,
            "runtime_id": self.runtime_id,
            "status": self.status,
            "metrics": [list(m) for m in self.metrics],
            "health": self.health,
            "snapshot_hash": self.snapshot_hash,
        }


@dataclass(frozen=True)
class RuntimeMetric:
    """Satu metrik runtime."""

    name: str
    value: Any
    unit: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "unit": self.unit}


class RuntimeObserver:
    """Observer kondisi runtime (read-only, tanpa mutation)."""

    def __init__(self) -> None:
        self._probes: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._snapshots: Tuple[RuntimeSnapshot, ...] = ()

    def register_probe(
        self, probe_id: str, fn: Callable[[], Dict[str, Any]]
    ) -> None:
        self._probes[probe_id] = fn

    def observe(self, runtime_id: str = "runtime") -> RuntimeSnapshot:
        status = "ok"
        metrics: List[RuntimeMetric] = []
        health_levels: List[str] = []
        for _pid, fn in self._probes.items():
            try:
                data = fn()
                for key, value in data.items():
                    if key == "status":
                        status = str(value)
                    elif key == "health":
                        health_levels.append(str(value))
                    else:
                        metrics.append(RuntimeMetric(key, value))
            except Exception:
                # probe gagal = status degraded (observasi tetap berjalan)
                status = "degraded"
                health_levels.append("unknown")
        health = self._aggregate_health(health_levels)
        snapshot = RuntimeSnapshot(
            captured_at=_now_utc(),
            runtime_id=runtime_id,
            status=status,
            metrics=tuple((m.name, m.value) for m in metrics),
            health=health,
            snapshot_hash=self._hash(status, health, metrics),
        )
        self._snapshots += (snapshot,)
        return snapshot

    @staticmethod
    def _aggregate_health(levels: List[str]) -> str:
        if any(level == "critical" for level in levels):
            return "critical"
        if any(level == "degraded" for level in levels):
            return "degraded"
        if any(level == "warning" for level in levels):
            return "warning"
        if levels and all(level == "healthy" for level in levels):
            return "healthy"
        return "unknown"

    @staticmethod
    def _hash(status: str, health: str, metrics: List[RuntimeMetric]) -> str:
        import hashlib

        h = hashlib.sha256()
        for part in (status, health, *[f"{m.name}={m.value}" for m in metrics]):
            h.update(str(part).strip().lower().encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def last_snapshot(self) -> Optional[RuntimeSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def all_snapshots(self) -> Tuple[RuntimeSnapshot, ...]:
        return self._snapshots


class RuntimeObservationReporter:
    """Menyusun laporan observasi runtime. Read-only."""

    @staticmethod
    def build_report(
        snapshots: Tuple[RuntimeSnapshot, ...],
    ) -> Dict[str, Any]:
        return {
            "observed_at": _now_utc(),
            "snapshot_count": len(snapshots),
            "latest": snapshots[-1].as_dict() if snapshots else None,
            "history": [s.as_dict() for s in snapshots],
        }

    @staticmethod
    def to_evidence(
        snapshot: RuntimeSnapshot,
        investigation_id: str,
        source_id: str = "runtime_observer",
    ) -> EvidenceModel:
        metric_data = {k: v for k, v in snapshot.metrics}
        metric_data["status"] = snapshot.status
        metric_data["health"] = snapshot.health
        return EvidenceModel(
            evidence_id=f"rt-{snapshot.snapshot_hash[:12]}",
            investigation_id=investigation_id,
            source=EvidenceSource("runtime", source_id, "runtime_observer"),
            category="runtime_observation",
            data=tuple(sorted(metric_data.items())),
            collected_at=snapshot.captured_at,
            metadata=(("captured_at", snapshot.captured_at),),
            validated=True,
        )
