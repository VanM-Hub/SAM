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

    AD-ENG-006 (Mission-Scoped Decision Targeting):
      `persistence_unit` opsional (PersistenceUnit yang SAMA dengan enumerasi
      Mission List, dari route). Bila diberikan, `decide` fallback dari live
      registry ke durable repository (`registry miss != mission missing`, AD-ENG-005
      §3.2) — sehingga mission yang hanya ada durable (pasca-restart) TETAP dapat
      di-decide, tenant-scoped. Tanpa `persistence_unit`, perilaku lama (KeyError
      jika tidak ada di live) dipertahankan penuh.
    """

    def __init__(
        self,
        service_factory: Optional[callable] = None,
        persistence_unit: Optional[object] = None,
    ) -> None:
        # mission_id -> (tenant, MissionUXService) ; exec_id -> mission service
        self._missions: Dict[str, Any] = {}
        self._registry = MissionRegistry()
        self._factory = service_factory  # memungkinkan inject utk test
        # AD-ENG-006 §5.3: durable repository + unit utk fallback & persist pasca-eksekusi.
        # Sumber durable = unit yang SAMA dengan enumerasi Mission List (route).
        self._persistence_unit = persistence_unit
        self._mission_repo = (
            getattr(persistence_unit, "missions", None) if persistence_unit is not None else None
        )

    def create(self, tenant: str = "default", mission_id: Optional[str] = None) -> Dict[str, str]:
        """Buat mission baru dengan state OTONOM. Return {tenant, mission_id}."""
        mid = mission_id or make_mission_id()
        svc = self._factory() if self._factory else _default_svc_factory()
        self._missions[mid] = {"tenant": _norm_tenant(tenant), "service": svc}
        return {"tenant": _norm_tenant(tenant), "mission_id": mid}

    def register(
        self, tenant: str, mission_id: str, service, execution_id: Optional[str] = None
    ) -> str:
        """Daftarkan mission-* eksisting ke live registry (tanpa Mission kedua).

        Dipakai utk mission yang dibentuk lewat jalur non-multi (mis. `/ux/submit`
        singleton, AD-ENG-006 kompatibilitas) agar tetap bisa ditarget oleh
        `decide` via MultiMissionService boundary. TIDAK menciptakan identity
        kedua: `service` adalah instance MissionUXService pemilik mission tsb
        (identity canonical mission-* sama). `execution_id` default = mission_id
        (konsisten dgn submit_mission).
        """
        mid = (mission_id or "").strip()
        if not mid:
            raise ValueError("mission_id wajib utk register ke registry")
        t = _norm_tenant(tenant)
        self._missions[mid] = {
            "tenant": t,
            "service": service,
            "registered": False,
        }
        snapshot = getattr(service, "get_state", None)
        st = snapshot() if callable(snapshot) else None
        if st is not None:
            self._registry.save(
                t, mid, execution_id or mid, st.as_dict()
            )
            # AD-ENG-006/UI-2: sinkronkan ke durable repo (bila ada) agar mission
            # dari jalur singleton `/ux/submit` TURUT di-enumerasi Mission List
            # (`/ux/missions` membaca repo durable + overlay registry). Tanpa ini,
            # mission `/ux/submit` tidak bisa dipilih user di UI utk di-approve.
            # TIDAK membuat Mission identity kedua: snapshot yang sama dgn state
            # canonical mission-* (satu aggregate, satu identity).
            if self._mission_repo is not None and callable(
                getattr(self._mission_repo, "save_mission", None)
            ):
                try:
                    # signature repo durable (MissionRepository Protocol):
                    # save_mission(mission_id, data). Tenant utk enumerasi
                    # dipegang registry (`/ux/missions` baca key tenant default).
                    self._mission_repo.save_mission(mid, st.as_dict())
                except Exception:  # pragma: no cover — hindari merusak registry
                    pass
        return mid

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

    def submit_mission(
        self,
        tenant: str,
        text: str,
        idempotency_key: str = None,
    ) -> "object":
        """Opsi-2 orchestration (AD-ENG-005 §7): MissionUXService -> register mission-*.

        Boundary COORDINATION/REGISTRATION utk Mission yang lahir dari
        Conversation. TIDAK membuat Mission kedua, TIDAK membuat m_* baru,
        TIDAK mengubah semantic contract `MissionUXService.submit()`.

        Flow:
          1. panggil MissionUXService.submit(text)  -> pembentukan Mission +
             persist (bila svc punya persistence); menghasilkan canonical
             mission-*.
          2. ambil `mission_id = observability.mission_id` (canonical mission-*).
          3. register mission-* + snapshot state ke MissionRegistry keyed
             canonical mission-* (runtime projection utk Mission List overlay).

        Returns:
            UxMissionState (canonical state; caller bisa `.as_dict()`).

        Executes `svc.submit()` (bukan `create()+submit`) sehingga TIDAK ada
        mission_id kedua: satu aggregate, satu canonical identity.
        """
        from sam.application.ux.service import MissionUXService

        svc: MissionUXService = (
            self._factory() if self._factory else _default_svc_factory()
        )
        st = svc.submit(text, idempotency_key=idempotency_key)
        mission_id = (st.observability or {}).get("mission_id") or st.request_id or ""
        # Register runtime projection keyed CANONICAL mission-* (bukan m_*,
        # bukan Mission kedua). execution_id diisi mission_id mengikuti contract
        # existing registry/submit (execution_id confusion tetap follow-up).
        if mission_id:
            self._registry.save(
                _norm_tenant(tenant), mission_id, mission_id, st.as_dict()
            )
            # Catat mission_id -> tenant utk isolasi & mission_count (tanpa
            # membuat instance MissionUXService kedua utk identity; svc di sini
            # milik alur ini).
            self._missions[mission_id] = {
                "tenant": _norm_tenant(tenant),
                "service": svc,
                "registered": True,
            }
        return st


    def decide(
        self, tenant: str, mission_id: str, execution_id: str, intent: str, approver: str = "user"
    ) -> dict:
        """Decision targeting (AD-ENG-006): resolve target mission dulu, baru decide.

        Resolution (tenant, mission_id):
          live registry > durable repository.
          - Mission ada di live (`_missions`, OTONOM)      -> pakai service live.
          - Mission tidak live tetapi ada durable (repo)   -> rehydrate service ke
            live (registry miss != mission missing), lalu decide.
          - Tidak ada di live ATAU durable                  -> KeyError -> route 404
            (zero mutation; TIDAK ada fallback ke current/latest/request_id/m_*).

        `intent = "approve" | "reject"`. Governance tetap didelegasikan ke
        `MissionUXService.decide(...)` (boundary canonical SAMA, tanpa orchestration
        kedua — AD-ENG-006 §5.2).
        """
        svc = self._resolve_service(tenant, mission_id)
        from sam.application.ux.approval import ApprovalDecisionIntent
        st = svc.decide(ApprovalDecisionIntent(intent), approver=approver)
        self._registry.save(tenant, mission_id, execution_id, st.as_dict())
        return st.as_dict()

    def _resolve_service(self, tenant: str, mission_id: str):
        """Resolve service mission target (live > durable). Tenant-scoped.

        - live: mission ada di `_missions` milik tenant -> return service live.
        - durable: mission tidak live tapi `self._mission_repo` memuatnya ->
          rehydrate service ke live (registry miss != mission missing) -> return.
        - miss keduanya -> KeyError (fail-closed; route -> 404).
        """
        t = _norm_tenant(tenant)
        # 1) live registry
        rec = self._missions.get(mission_id)
        if rec is not None:
            if rec["tenant"] != t:
                raise KeyError(
                    f"cross-tenant DENIED: mission {mission_id} bukan milik tenant ini"
                )
            return rec["service"]
        # 2) durable repository (registry miss != mission missing)
        if self._mission_repo is not None:
            state_dict = self._mission_repo.load_mission(mission_id)
            if state_dict is not None:
                svc = self._hydrate_service(t, mission_id, state_dict)
                self._missions[mission_id] = {
                    "tenant": t,
                    "service": svc,
                    "registered": True,
                }
                return svc
        # 3) miss keduanya -> fail-closed
        raise KeyError(
            f"mission tidak dikenal (isolasi, tanpa state global): {mission_id}"
        )

    def _hydrate_service(self, tenant: str, mission_id: str, state_dict: dict):
        """Bangun service MissionUXService yang di-rehydrate dari state durable.

        Agar `MissionUXService.decide()` dapat berjalan terhadap mission yang
        tidak live (pasca-restart), service dibangun dengan `_state`, `_request`,
        `_plan`, dan pending `_approval` yang direstore dari `state_dict` — tanpa
        mengubah semantic contract `MissionUXService` (AD-ENG-006 §8.2). Tidak
        ada identitas baru; canonical `mission-*` tetap dipertahankan.
        """
        from sam.application.ux.service import MissionUXService
        from sam.application.ux.mission_request import (
            MissionRequest,
            MissionRequestStatus,
        )
        from sam.application.ux.plan import MissionPlan, MissionPlanStatus
        from sam.application.ux.approval import ApprovalRequest
        from sam.application.ux.state import UxMissionState, UxStateStatus

        understanding = state_dict.get("understanding") or {}
        plan = state_dict.get("plan") or {}
        approval = state_dict.get("approval") or {}
        execution = state_dict.get("execution") or {}
        obs = state_dict.get("observability") or {}
        request_id = state_dict.get("request_id") or obs.get("request_id") or ""
        text = state_dict.get("request") or ""
        operation = understanding.get("operation") or ""
        target = understanding.get("target") or ""

        # Service via factory (BUKAN `_default_svc_factory()`) agar unit persistence
        # yang di-inject factory route tetap dipakai (persist hasil decide bisa
        # ditulis ke repo yang sama).
        svc: MissionUXService = (
            self._factory() if self._factory else _default_svc_factory()
        )
        svc._request = MissionRequest(
            request_id=request_id,
            text=text,
            operation=operation,
            target=target,
            status=MissionRequestStatus.UNDERSTOOD,
        )
        svc._plan = MissionPlan(
            plan_id=state_dict.get("plan_id") or f"plan-{mission_id[:8]}",
            request_id=request_id,
            what_sam_understood=understanding.get("what_sam_understood") or "",
            planned_steps=list(plan.get("planned_steps", [])),
            approval_required=bool(plan.get("approval_required", False)),
            approval_reason="",
            status=(
                MissionPlanStatus.PENDING_APPROVAL
                if str(approval.get("status", "")) == "waiting_approval"
                else MissionPlanStatus.DRAFT
            ),
        )
        st = UxMissionState()
        st.request_id = request_id
        st.request_text = text
        st.what_sam_understood = understanding.get("what_sam_understood") or ""
        st.operation = operation
        st.target = target
        st.planned_steps = list(plan.get("planned_steps", []))
        st.approval_required = bool(plan.get("approval_required", False))
        st.action_summary = plan.get("action_summary", "")
        st.approval_status = approval.get("status") or UxStateStatus.NONE
        st.approval_decision = approval.get("decision")
        st.status = execution.get("status") or UxStateStatus.NONE
        st.failure_kind = execution.get("failure_kind") or ""
        st.failure_message = execution.get("failure_message") or ""
        st.result_summary = execution.get("result_summary") or ""
        st.evidence = list(state_dict.get("evidence", []))
        st.artifact_ref = state_dict.get("artifact_ref", "")
        st.audit_ref = state_dict.get("audit_ref", "")
        st.timeline = list(state_dict.get("timeline", []))
        st.observability = dict(obs)
        if mission_id:
            obs2 = dict(st.observability)
            obs2["mission_id"] = mission_id
            st.observability = obs2
        st.updated_at = state_dict.get("updated_at", st.updated_at)
        svc._state = st
        svc._last_result = None
        svc._audit = list(svc._audit)
        # Restore pending approval utk mission yang masih WAITING_APPROVAL sehingga
        # `MissionUXService.decide()` (-> ApprovalCoordinator.decide) tidak raise
        # "tidak ada pending approval". Approval yang sudah diputuskan (APROVED/REJECTED)
        # TIDAK dijadikan pending (repeated decision mengikuti idempotency existing).
        if st.approval_required and str(st.approval_status) == UxStateStatus.WAITING_APPROVAL:
            pending = ApprovalRequest(
                approval_id=obs.get("request_id") or f"apr-{mission_id[:8]}",
                plan_id=svc._plan.plan_id,
                request_id=request_id,
                action_summary=st.action_summary or (
                    f"SAM akan: {st.planned_steps[0] if st.planned_steps else 'menjalankan tindakan'}"
                ),
                gates=list(st.planned_steps),
            )
            svc._approval.record_pending(pending)
        # Pastikan persistence unit yang SAMA dipertahankan (persist pasca-decide
        # menulis kembali ke repo yang sama — deterministik, sinkron dev/prod).
        if self._persistence_unit is not None:
            svc._persistence = self._persistence_unit
        return svc

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
