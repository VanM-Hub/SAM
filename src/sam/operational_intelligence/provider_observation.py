"""Provider Observation - WP-05 (MISSION-4.2 / IP-4.2-001).

Mengamati kondisi Provider sebagai bagian dari investigasi. Provider diamati
tanpa execution, status tervalidasi, observation menghasilkan evidence,
observation dapat diaudit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from .evidence_collection import EvidenceModel, EvidenceSource


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class ProviderHealth:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderSnapshot:
    """Snapshot kondisi provider (immutable, tanpa execution)."""

    provider_id: str
    captured_at: str
    health: str = ProviderHealth.UNKNOWN
    available: bool = False
    metrics: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)
    snapshot_hash: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "captured_at": self.captured_at,
            "health": self.health,
            "available": self.available,
            "metrics": [list(m) for m in self.metrics],
            "snapshot_hash": self.snapshot_hash,
        }


class ProviderObservation:
    """Hasil observasi provider (dapat diaudit)."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id
        self._snapshots: Tuple[ProviderSnapshot, ...] = ()

    def record(self, snapshot: ProviderSnapshot) -> None:
        self._snapshots += (snapshot,)

    def last(self) -> Optional[ProviderSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def all(self) -> Tuple[ProviderSnapshot, ...]:
        return self._snapshots

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "snapshots": [s.as_dict() for s in self._snapshots],
            "auditable": True,
        }


class ProviderAvailabilityEvaluator:
    """Menilai ketersediaan provider berdasarkan snapshot (deterministik)."""

    @staticmethod
    def evaluate(snapshot: ProviderSnapshot) -> bool:
        if snapshot.health == ProviderHealth.HEALTHY:
            return True
        if snapshot.health == ProviderHealth.DEGRADED:
            return True
        return False


class ProviderObserver:
    """Observer registry provider (read-only)."""

    def __init__(self) -> None:
        self._probes: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._observations: Dict[str, ProviderObservation] = {}

    def register_probe(
        self, provider_id: str, fn: Callable[[], Dict[str, Any]]
    ) -> None:
        self._probes[provider_id] = fn
        self._observations.setdefault(provider_id, ProviderObservation(provider_id))

    def observe(self, provider_id: str) -> Optional[ProviderSnapshot]:
        fn = self._probes.get(provider_id)
        if fn is None:
            return None
        try:
            data = fn()
        except Exception:
            data = {"health": ProviderHealth.UNREACHABLE, "available": False}
        health = str(data.get("health", ProviderHealth.UNKNOWN))
        available = self._normalize_available(data, health)
        metrics = tuple(
            sorted(
                {
                    k: v
                    for k, v in data.items()
                    if k not in ("health", "available")
                }.items()
            )
        )
        snapshot = ProviderSnapshot(
            provider_id=provider_id,
            captured_at=_now_utc(),
            health=health,
            available=available,
            metrics=metrics,
            snapshot_hash=self._hash(provider_id, health, available, metrics),
        )
        self._observations.setdefault(provider_id, ProviderObservation(provider_id)).record(
            snapshot
        )
        return snapshot

    @staticmethod
    def _normalize_available(data: Dict[str, Any], health: str) -> bool:
        if "available" in data:
            return bool(data["available"])
        return ProviderAvailabilityEvaluator.evaluate(
            ProviderSnapshot(
                provider_id="",
                captured_at="",
                health=health,
            )
        )

    @staticmethod
    def _hash(
        provider_id: str, health: str, available: bool, metrics: Any
    ) -> str:
        import hashlib

        h = hashlib.sha256()
        for part in (
            provider_id,
            health,
            available,
            *[f"{k}={v}" for k, v in metrics],
        ):
            h.update(str(part).strip().lower().encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def observation(self, provider_id: str) -> Optional[ProviderObservation]:
        return self._observations.get(provider_id)

    def list_providers(self) -> Tuple[str, ...]:
        return tuple(self._probes.keys())


class ProviderObservationReporter:
    """Menyusun laporan observasi provider. Read-only."""

    @staticmethod
    def build_report(
        observation: ProviderObservation,
    ) -> Dict[str, Any]:
        return {
            "reported_at": _now_utc(),
            "provider_id": observation.provider_id,
            "latest": observation.last().as_dict() if observation.last() else None,
            "history": [s.as_dict() for s in observation.all()],
        }

    @staticmethod
    def to_evidence(
        snapshot: ProviderSnapshot,
        investigation_id: str,
    ) -> EvidenceModel:
        return EvidenceModel(
            evidence_id=f"pv-{snapshot.snapshot_hash[:12]}",
            investigation_id=investigation_id,
            source=EvidenceSource("provider", snapshot.provider_id, "provider_observer"),
            category="provider_observation",
            data=tuple(sorted(snapshot.metrics) + [("health", snapshot.health)]),
            collected_at=snapshot.captured_at,
            metadata=(("available", str(snapshot.available)),),
            validated=True,
        )
