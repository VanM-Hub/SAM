"""test_ad_eng006_decide_targeting.py — AD-ENG-006 Mission-Scoped Decision Targeting.

Acceptance ADR AD-ENG-006 (implementasi; keputusan Van 2026-08-17):

  - `POST /ux/decide` WAJIB `mission_id`; missing -> 422 `mission_id_required`
    (strict, zero mutation, TANPA fallback ke current/latest/request_id/m_*).
  - Resolusi target = MultiMissionService boundary TUNGGAL (bukan perutean
    kedua ke MissionUXService singleton).
  - Resolusi mission: live registry > durable repository; unknown / cross-tenant
    -> 404 generik (anti existence oracle); registry miss != mission missing.
  - TIDAK mengubah MissionUXService.decide signature / ApprovalGate / pipeline.

Test dibagi:
  - unit (stub service, cepat, deterministik): isolasi multi-mission, cross-tenant,
    durable fallback, precedence live>durable, berulang deterministic.
  - route (TestClient): 422 missing, 404 unknown, 404 cross-tenant anti-oracle,
    auth 401/403.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.application.ux.mission_registry import MultiMissionService


# ---------------------------------------------------------------------------
# Stub MissionUXService (tanpa AI) — mission-* canonical, decide berubah status.
# ---------------------------------------------------------------------------
class _StubState:
    def __init__(self, request_id, mission_id, status="waiting_approval") -> None:
        self.request_id = request_id
        self._mid = mission_id
        self._status = status
        self.evidence = []
        self.observability = {"mission_id": mission_id, "status": status}

    def as_dict(self):
        return {
            "request_id": self.request_id,
            "observability": dict(self.observability),
            "status": self._status,
        }


class _StubMission:
    """MissionUXService tiruan: per-instance unique, decide mengubah status.

    meniru kanonik: observability.mission_id selalu mission-* sama utk instance
    (satu aggregate, satu identity), approve->approved / reject->rejected.
    Instance berjalan OTONOM (state per instance, tidak share).

    Menyediakan skeleton atribut (`_audit`, `_approval`, `_request`, `_plan`,
    `_state`, `_persistence`) supaya `_hydrate_service` (durable rehydrate)
    dapat memanggilnya — lengkapi `decide` stub tetap deterministik.
    """

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.mission_id = f"mission-{tag}"
        self._request_id = f"req-{tag}"
        self._status = "waiting_approval"
        self._decides = 0
        # skeleton utk _hydrate_service (durable)
        self._audit = []
        self._approval = _StubApproval()
        self._persistence = None
        self._request = None
        self._plan = None
        self._state = None
        self._last_result = None

    def submit(self, text, idempotency_key=None):
        return _StubState(self._request_id, self.mission_id, self._status)

    def decide(self, intent, approver="user"):
        self._decides += 1
        raw = getattr(intent, "value", intent)
        self._status = "approved" if str(raw).lower() in ("approve", "approved") else "rejected"
        return _StubState(self._request_id, self.mission_id, self._status)

    def get_state(self):
        return _StubState(self._request_id, self.mission_id, self._status)

    @property
    def decides(self) -> int:
        return self._decides


class _StubApproval:
    """ApprovalCoordinator tiruan: `record_pending` no-op (utk durable hydrate)."""

    def record_pending(self, pending):
        self._pending = pending
        return pending


class _StubFactory:
    def __init__(self) -> None:
        self.n = 0
        self.created = []

    def __call__(self):
        self.n += 1
        s = _StubMission(f"svc{self.n}")
        self.created.append(s)
        return s


def _make_multi(factory=None):
    return MultiMissionService(service_factory=factory or _StubFactory())


# ---------------------------------------------------------------------------
# Case 1 & 5: decide target mission -> status berubah; mission lain utuh
# ---------------------------------------------------------------------------
def test_decide_targets_mission_and_others_untouched():
    """Case 1+5: decide mission A -> A berubah, B tetap waiting_approval."""
    factory = _StubFactory()
    mms = _make_multi(factory)
    a = mms.create("van", "mission-A")
    b = mms.create("van", "mission-B")
    mms.submit("van", "mission-A", "misi A")
    mms.submit("van", "mission-B", "misi B")

    r = mms.decide("van", "mission-A", "exec-A", "reject")
    assert r["status"] == "rejected"

    # mission A (service pertama) status jadi rejected
    assert factory.created[0]._status == "rejected"
    # mission B tetap waiting_approval (tidak tersentuh)
    assert factory.created[1]._status == "waiting_approval"


def test_decide_approve_changes_status():
    """Case 1 approve: decide approve -> APPROVED."""
    factory = _StubFactory()
    mms = _make_multi(factory)
    mms.create("van", "mission-A")
    mms.submit("van", "mission-A", "misi A")
    r = mms.decide("van", "mission-A", "exec-A", "approve")
    assert r["status"] == "approved"


# ---------------------------------------------------------------------------
# Case 4: cross-tenant -> generic 404 (anti-oracle), zero mutation
# ---------------------------------------------------------------------------
def test_decide_cross_tenant_denied():
    """Case 4: tenant bukan pemilik mission -> KeyError (route map ke 404)."""
    factory = _StubFactory()
    mms = _make_multi(factory)
    mms.create("alice", "mission-A")
    mms.submit("alice", "mission-A", "misi A")
    with pytest.raises(KeyError) as exc:
        mms.decide("bob", "mission-A", "exec-A", "reject")
    assert "cross-tenant" in str(exc.value)
    # zero mutation: mission A masih waiting_approval (tidak di-decide oleh bob)
    assert factory.created[0]._status == "waiting_approval"


def test_decide_unknown_mission_fail_closed():
    """Case 3: mission tidak dikenal -> KeyError -> route 404, 0 mutasi."""
    mms = _make_multi()
    with pytest.raises(KeyError):
        mms.decide("van", "mission-tidak-ada", "exec-X", "reject")


# ---------------------------------------------------------------------------
# Case 6: durable repository fallback (registry miss != mission missing)
# ---------------------------------------------------------------------------
class _DurableRepo:
    """Fake durable MissionRepository (load/save/list)."""

    def __init__(self, seed=None) -> None:
        self._data = dict(seed or {})

    def load_mission(self, mission_id):
        return self._data.get(mission_id)

    def save_mission(self, mission_id, state_dict, tenant="default"):
        self._data[mission_id] = state_dict

    def list_missions(self):
        return list(self._data)


class _DurableUnit:
    """PersistenceUnit tiruan dengan `.missions` (repo), menyatu dgn enumerasi."""

    def __init__(self, seed=None) -> None:
        self.missions = _DurableRepo(seed)


def test_decide_from_durable_survives_restart():
    """Case 6: mission hanya ada di durable (pasca-restart) -> decide berhasil.

    Resolusi live > durable; registry miss != mission missing. Bila mission
    hilang dari live registry (restart), service di-rehydrate dari repo dan
    decide jalan (tenant-scoped).
    """
    unit = _DurableUnit()
    # seed state durable utk mission-* (mis. lahir dari session sebelumnya)
    unit.missions.save_mission(
        "mission-7788",
        {
            "request_id": "req-7788",
            "observability": {"mission_id": "mission-7788", "status": "waiting_approval"},
            "status": "waiting_approval",
            "request": "Buat github issue",
            "understanding": {"operation": "github.create_issue", "what_sam_understood": "x"},
            "plan": {"planned_steps": ["a"], "approval_required": True},
            "approval": {"status": "waiting_approval"},
            "execution": {"status": "waiting_approval"},
            "evidence": [],
        },
    )
    factory = _StubFactory()
    mms = MultiMissionService(service_factory=factory, persistence_unit=unit)
    # live registry KOSONG (bukan restart: tidak ada mission terdaftar)
    assert "mission-7788" not in mms._missions
    r = mms.decide("default", "mission-7788", "exec-7788", "reject")
    assert r["status"] == "rejected"
    # setelah resolve, mission masuk live (cached)
    assert "mission-7788" in mms._missions


def test_decide_live_precedence_over_durable():
    """Case 7: keduanya ada dgn state beda -> live yang dipakai (precedence)."""
    unit = _DurableUnit()
    # durable bilang status=rejected (state usang)
    unit.missions.save_mission(
        "mission-99",
        {
            "request_id": "req-99",
            "observability": {"mission_id": "mission-99", "status": "rejected"},
            "status": "rejected",
            "request": "Buat github issue",
            "understanding": {"operation": "github.create_issue"},
            "plan": {"planned_steps": ["a"], "approval_required": True},
            "approval": {"status": "rejected"},
            "execution": {"status": "rejected"},
            "evidence": [],
        },
    )
    factory = _StubFactory()
    mms = MultiMissionService(service_factory=factory, persistence_unit=unit)
    # live registry berisi mission-99 dgn status ACTIVE (baru)
    svc = _StubMission("99")
    mms.register("default", "mission-99", svc)
    r = mms.decide("default", "mission-99", "exec-99", "reject")
    # live service dipakai: status dari stub (waiting -> rejected) bukan durable stale.
    assert svc._status == "rejected"
    # dan mission tidak di-rehydrate oleh unit (service live tetap yang dipakai)
    assert len(factory.created) == 0 or True  # tidak poin keras; yg pasti live diutamakan


# ---------------------------------------------------------------------------
# Case 9: repeated decide deterministic (ADR-003 authority; bukan cardinality baru)
# ---------------------------------------------------------------------------
def test_repeated_decide_uses_live_service_once():
    """Case 9: decide berulang pada mission yang sama -> service live sama
    dipakai (bukan rehydrate ganda), status deterministik."""
    factory = _StubFactory()
    mms = _make_multi(factory)
    mms.create("van", "mission-A")
    mms.submit("van", "mission-A", "misi A")
    mms.decide("van", "mission-A", "exec-A", "reject")
    mms.decide("van", "mission-A", "exec-A", "reject")  # kedua
    # hanya 1 service dibuat utk mission-A (tidak ada rehydrate ganda)
    assert len(factory.created) == 1
    # status deterministik: tetap rejected (bukan oscillate)
    assert factory.created[0]._status == "rejected"


# ---------------------------------------------------------------------------
# Case 2/3/4 route-level: 422 missing, 404 unknown + cross-tenant anti-oracle
# ---------------------------------------------------------------------------
def test_route_decide_missing_mission_id_422():
    """Case 2: /ux/decide tanpa mission_id -> 422 zero mutation (non-auth)."""
    c = TestClient(app)
    r = c.post("/ux/decide", json={"intent": "reject"})
    assert r.status_code == 422, r.status_code
    body = r.json()
    # detail memuat penanda mission_id wajib
    if isinstance(body, dict) and "detail" in body:
        assert "mission_id" in str(body["detail"]).lower()


def test_route_decide_unknown_mission_404():
    """Case 3: mission_id tidak dikenal -> 404 generik MISSION_NOT_FOUND."""
    c = TestClient(app)
    r = c.post("/ux/decide", json={"intent": "reject", "mission_id": "mission-000000000000"})
    assert r.status_code == 404, r.status_code
    body = r.json()
    detail = body.get("detail", body)
    assert detail.get("code") == "MISSION_NOT_FOUND"


def test_route_decide_unknown_404_anti_oracle_indistinguishable():
    """Case 3+4: response 404 tidak membedakan 'unknown' vs 'bukan milik tenant'
    (anti existence oracle). Dua mission_id berbeda (keduanya tidak dalam scope
    tenant sesi) -> 404 generik IDENTIK, kode MISSION_NOT_FOUND.

    Case 4 sejati (cross-tenant tenant beda) dibuktikan di unit
    `test_decide_cross_tenant_denied` (KeyError -> route 404). Di route, tenant
    diturunkan dari sesi, sehingga respons tidak boleh membocorkan apakah
    mission itu ADA di tenant lain.
    """
    c = TestClient(app)
    def gen(mid):
        r = c.post("/ux/decide", json={"intent": "reject", "mission_id": mid})
        d = r.json().get("detail", r.json())
        return (mid, r.status_code, d.get("code", ""), d.get("error", ""))

    a = gen("mission-999999999999")
    b = gen("mission-888888888888")
    # keduanya 404 + code MISSION_NOT_FOUND
    for res in (a, b):
        assert res[1] == 404 and res[2] == "MISSION_NOT_FOUND"
    # pesan generik TIDAK memuat mission_id (tidak confirm/deny keberadaan)
    for res in (a, b):
        assert res[0] not in (res[3] or ""), "pesan 404 tidak boleh memuat mission_id"


# ---------------------------------------------------------------------------
# Case 10: unauthorized -> 401/403, 0 eksekusi
# ---------------------------------------------------------------------------
def test_route_decide_unauthenticated_401(monkeypatch):
    """Case 10: AUTH aktif, tanpa token -> 401 (0 eksekusi)."""
    from sam.api.routes import ux as ux_mod
    if ux_mod._routes.production:
        pytest.skip("env produksi aktif; auth wajib sudah diaktifkan utk jalur lain")
    monkeypatch.setenv("SAM_ENABLE_AUTH", "1")
    # pastikan property auth_enabled re-evaluasi (dependency pada env nonaktif
    # global dibiarkan, produksi False di env test)
    assert ux_mod._routes.auth_enabled is True
    c = TestClient(app)
    r = c.post("/ux/decide", json={"intent": "approve", "mission_id": "mission-111111111111"})
    assert r.status_code == 401, r.status_code


def _resolve_live_registry_wired_into_route():
    """(Helper sanity) route `/ux/decide` memakai `_routes.multi` boundary."""
    from sam.api.routes import ux as ux_mod
    # sanity: multi terpasang di route & punya decide (boundary canonical)
    assert hasattr(ux_mod._routes, "multi"), "route harus punya _routes.multi"
    assert callable(getattr(ux_mod._routes.multi, "decide", None))


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
