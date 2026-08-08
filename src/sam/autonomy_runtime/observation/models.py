# Runtime State Model - WP-01
# IP-3.2-001 Runtime Observation & Diagnostics (AO-3.2-001 / ED-3.2-001)
#
# Model data state runtime sebagai immutable DTO (ADR-023).
# Semua kelas di sini adalah data pasif; tidak ada logika aksi.
# Prinsip: Autonomy without Authority. Output = observasi, bukan aksi.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ComponentState:
    """Kondisi observasional satu komponen runtime (read-only)."""

    name: str
    kind: str  # e.g. "kernel", "provider", "repository", "gateway", "connector"
    status: str  # "ok" | "degraded" | "error" | "unknown"
    ready: bool
    dependencies: tuple = ()  # tuple[str] nama komponen yang menjadi prasyarat
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "ready": self.ready,
            "dependencies": list(self.dependencies),
            "detail": self.detail,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class RuntimeState:
    """State lengkap runtime pada satu titik amatan (immutable)."""

    state_id: str
    observed_at: str  # ISO-8601 timestamp
    status: str  # ringkasan: "ok" | "degraded" | "error"
    components: tuple = ()  # tuple[ComponentState]
    lifecycle_status: str = "unknown"
    readiness: str = "unknown"  # "ready" | "not_ready" | "unknown"
    health: str = "unknown"  # "healthy" | "degraded" | "unhealthy" | "unknown"
    failure: Optional[str] = None
    bottleneck: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "status": self.status,
            "components": [c.as_dict() for c in self.components],
            "lifecycle_status": self.lifecycle_status,
            "readiness": self.readiness,
            "health": self.health,
            "failure": self.failure,
            "bottleneck": self.bottleneck,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Snapshot ringan (id + waktu + ringkasan) untuk riwayat observasi."""

    snapshot_id: str
    state_id: str
    observed_at: str
    status: str
    checksum: str  # deterministik dari state (untuk deteksi perubahan)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "status": self.status,
            "checksum": self.checksum,
        }
