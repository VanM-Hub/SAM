"""mission_registry.py — M12-012 Multi-Mission Isolation.

Tujuan: state mission TIDAK disimpan sebagai "state global tunggal" pada satu
authority. Setiap state di-key-kan secara eksplisit per:

    (tenant, mission_id, execution_id)

Tanpa adanya `self._state` global pada registry — semua operasi membaca/menulis
Wajib menyertakan key. Ini mencegah kebocoran antar-tenant / antar-mission /
antar-execution (cross-tenant DENIED, cross-mission DENIED).

Komponen:
  - MissionRegistry  : store nilai (state apa pun, biasanya dict UxMissionState
                       as_dict) yang di-key-kan per (tenant, mission_id,
                       execution_id). HANYA pemilik key yang bisa akses.
  - MultiMissionService : adapter Application-layar yang mengelola beberapa
                       mission paralel, Tiap mission memegang instance
                       MissionUXService OTONOM (state ter-isolasi per mission),
                       diindeks di registry. Operasi selalu lewat key eksplisit;
                       tanpa/tak dikenal key -> KeyError (bukan fallback state
                       global).

Desain keputusan M12-012:
  - MissionUXService jalur single-mission produksi (M9/M10/M11) tetap dipakai
    utk regresi & kompatibilitas. MultiMissionService menambah kapabilitas
    multi-mission TER-ISOLASI tanpa merombak jalur yang sudah terbukti.
  - Tidak ada state global di level registry; key wajib eksplisit.
"""
from __future__ import annotations

import secrets
from typing import Any, Dict, Optional, Tuple

# Key tuple: (tenant, mission_id, execution_id)
MissionKey = Tuple[str, str, str]


def make_mission_id() -> str:
    """Buat mission_id acak (urlsafe)."""
    return "m_" + secrets.token_urlsafe(8)


def make_execution_id() -> str:
    return "x_" + secrets.token_urlsafe(8)


def _norm_tenant(tenant: str) -> str:
    return (tenant or "default").strip() or "default"


class MissionRegistry:
    """Store state yang di-key-kan per (tenant, mission_id, execution_id).

    - save(key, value)   : simpan/update state utk key.
    - get(key)           : kembalikan state utk key; None bila tak ada.
    - delete(key)        : hapus state utk key.
    - list_keys(tenant?, mission_id?) : enumerasi key (filter opsional).
    - Isolasi: key TIDAK bisa di-akses lintas pemilik; tanpa key -> tidak ada
      "state saat ini" yang bisa dipegang global.
    """

    def __init__(self) -> None:
        self._entries: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    def _key(self, tenant: str, mission_id: str, execution_id: str) -> MissionKey:
        if not mission_id:
            raise ValueError("mission_id wajib (tanpa state global)")
        return (_norm_tenant(tenant), mission_id, (execution_id or "") or "")

    def save(
        self, tenant: str, mission_id: str, execution_id: str, value: Any
    ) -> MissionKey:
        key = self._key(tenant, mission_id, execution_id)
        self._entries[key] = value
        return key

    def get(
        self, tenant: str, mission_id: str, execution_id: Optional[str] = None
    ) -> Optional[Any]:
        key = self._key(tenant, mission_id, execution_id or "")
        return self._entries.get(key)

    def has(self, tenant: str, mission_id: str, execution_id: Optional[str] = None) -> bool:
        return self.get(tenant, mission_id, execution_id) is not None

    def delete(self, tenant: str, mission_id: str, execution_id: Optional[str] = None) -> bool:
        key = self._key(tenant, mission_id, execution_id or "")
        if key in self._entries:
            del self._entries[key]
            return True
        return False

    def list_keys(self, tenant: Optional[str] = None, mission_id: Optional[str] = None) -> list:
        tenant = _norm_tenant(tenant) if tenant is not None else None
        out = []
        for (t, m, x) in self._entries:
            if tenant is not None and t != tenant:
                continue
            if mission_id is not None and m != mission_id:
                continue
            out.append({"tenant": t, "mission_id": m, "execution_id": x})
        return out

    def clear(self, tenant: Optional[str] = None) -> int:
        """Hapus semua entry (bila tenant diberikan, hanya tenant tsb)."""
        if tenant is None:
            n = len(self._entries)
            self._entries.clear()
            return n
        t = _norm_tenant(tenant)
        to_del = [k for k in self._entries if k[0] == t]
        for k in to_del:
            del self._entries[k]
        return len(to_del)

    def size(self) -> int:
        return len(self._entries)


class MultiMissionService:
    """Adapter multi-mission: tiap mission = MissionUXService OTONOM ter-isolasi.

    - create(tenant, mission_id=None) -> mission_id baru; instance service dibuat
      terpisah (tidak share state antar mission).
    - submit/decide/get_state: selalu lewat (tenant, mission_id[, execution_id]).
      Tanpa mission yang dikenal -> KeyError (bukan state global).
    - Isolasi cross-tenant/cross-mission: service instance A tidak dijangkau
      dari key B (registry keyed oleh pemilik).
    """

    def __init__(self, service_factory: Optional[callable] = None) -> None:
        # mission_id -> (tenant, MissionUXService) ; exec_id -> mission service
        self._missions: Dict[str, Any] = {}
        self._registry = MissionRegistry()
        self._factory = service_factory  # memungkinkan inject utk test

    def create(self, tenant: str = "default", mission_id: Optional[str] = None) -> Dict[str, str]:
        """Buat mission baru dengan state OTONOM. Return {tenant, mission_id}."""
        mid = mission_id or make_mission_id()
        svc = self._factory() if self._factory else _default_svc_factory()
        self._missions[mid] = {"tenant": _norm_tenant(tenant), "service": svc}
        return {"tenant": _norm_tenant(tenant), "mission_id": mid}

    def _service(self, tenant: str, mission_id: str):
        rec = self._missions.get(mission_id)
        if not rec:
            raise KeyError(f"mission tidak dikenal (isolasi, tanpa state global): {mission_id}")
        if rec["tenant"] != _norm_tenant(tenant):
            raise KeyError("cross-tenant DENIED: mission bukan milik tenant ini")
        return rec["service"]

    def submit(self, tenant: str, mission_id: str, text: str, idempotency_key: str = None) -> dict:
        svc = self._service(tenant, mission_id)
        st = svc.submit(text, idempotency_key=idempotency_key)
        # simpan snapshot per execution (key: mission_id + request_id sbagai execution)
        execution_id = (st.observability or {}).get("mission_id") or st.request_id
        self._registry.save(
            tenant, mission_id, execution_id, st.as_dict()
        )
        return st.as_dict()

    def decide(
        self, tenant: str, mission_id: str, execution_id: str, intent: str, approver: str = "user"
    ) -> dict:
        svc = self._service(tenant, mission_id)
        from sam.application.ux.approval import ApprovalDecisionIntent
        st = svc.decide(ApprovalDecisionIntent(intent), approver=approver)
        self._registry.save(tenant, mission_id, execution_id, st.as_dict())
        return st.as_dict()

    def get_state(self, tenant: str, mission_id: str, execution_id: str = None) -> Optional[dict]:
        # dari registry (source of truth snapshot), bukan state global
        return self._registry.get(tenant, mission_id, execution_id)

    def registry(self) -> MissionRegistry:
        return self._registry

    def mission_count(self) -> int:
        return len(self._missions)


def _default_svc_factory():
    from sam.application.ux.service import MissionUXService
    return MissionUXService()
