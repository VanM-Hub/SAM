# Runtime Observation Engine - WP-02
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Mesin observasi: berjalan skenario 'yang berjarak amat' atas penyedia
# komponen, menghasilkan RuntimeState + RuntimeSnapshot (checksum deterministik).
# Hanya membaca; TIDAK mengubah lifecycle, TIDAK recovery, TIDAK restart,
# TIDAK scheduling, TIDAK orchestration.

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sam.autonomy_runtime.observation.models import (
    ComponentState,
    RuntimeSnapshot,
    RuntimeState,
)


# Penyedia komponen: callable(name) -> Dict[str, Any] yang mengamati satu
# komponen dan mengembalikan dict observasi (status/ok/ready/detail/data).
ComponentProbe = Callable[[str], Dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return "{}:{}".format(prefix, digest)


def _state_checksum(state: RuntimeState) -> str:
    payload = json.dumps(state.as_dict(), sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


class ObservationEngine:
    """Mengamati runtime dan menghasilkan state/snapshot (read-only)."""

    def __init__(self, probes: Optional[Dict[str, ComponentProbe]] = None):
        self._probes: Dict[str, ComponentProbe] = dict(probes or {})

    def register(self, name: str, probe: ComponentProbe) -> None:
        """Daftarkan probe observasi untuk satu komponen."""
        self._probes[name] = probe

    def component_names(self) -> List[str]:
        return sorted(self._probes.keys())

    def observe_component(self, name: str, timestamp: str) -> ComponentState:
        """Observer satu komponen. Tidak pernah fallback ke mutasi."""
        probe = self._probes.get(name)
        if probe is None:
            return ComponentState(
                name=name,
                kind="unknown",
                status="unknown",
                ready=False,
                detail="no probe registered",
            )
        try:
            raw = probe(name) or {}
            kind = str(raw.get("kind", "component"))
            status = str(raw.get("status", "unknown"))
            ready = bool(raw.get("ready", False))
            deps = tuple(str(d) for d in raw.get("dependencies", ()))
            detail = str(raw.get("detail", ""))
            data = dict(raw.get("data", {}))
            return ComponentState(
                name=name,
                kind=kind,
                status=status,
                ready=ready,
                dependencies=deps,
                detail=detail,
                data=data,
            )
        except Exception as exc:  # observasi gagal -> dilaporkan, bukan dicegah
            return ComponentState(
                name=name,
                kind="component",
                status="error",
                ready=False,
                detail="probe raised: {}: {}".format(type(exc).__name__, exc),
            )

    def observe(self, timestamp: Optional[str] = None) -> RuntimeState:
        """Ambil state penuh runtime dari seluruh probe terdaftar."""
        ts = timestamp or _utc_now()
        if not self._probes:
            return RuntimeState(
                state_id=_make_id("state", ts),
                observed_at=ts,
                status="unknown",
                metadata={"probed": 0},
            )
        components = tuple(
            self.observe_component(name, ts) for name in self.component_names()
        )
        # Agregasi status deterministik: error > degraded > ok > unknown
        if any(c.status == "error" for c in components):
            status = "error"
        elif any(c.status == "degraded" for c in components):
            status = "degraded"
        elif all(c.status == "ok" for c in components):
            status = "ok"
        else:
            status = "unknown"
        state = RuntimeState(
            state_id=_make_id("state", ts),
            observed_at=ts,
            status=status,
            components=components,
            metadata={"probed": len(components), "registered": len(self._probes)},
        )
        return state

    def snapshot(self, state: Optional[RuntimeState] = None) -> RuntimeSnapshot:
        """Buat snapshot ringan ber-checksum deterministik dari state."""
        st = state or self.observe()
        checksum = _state_checksum(st)
        return RuntimeSnapshot(
            snapshot_id=_make_id("snap", st.state_id),
            state_id=st.state_id,
            observed_at=st.observed_at,
            status=st.status,
            checksum=checksum,
        )
