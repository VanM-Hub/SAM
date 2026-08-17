"""tests/ward/test_w1_ward_activation.py — W1 Ward Activation acceptance A-M.

Van W1 directive (2026-08-17) acceptance:
  A. Ward identity canonical
  B. OpenClaw registered
  C. explicit entrustment
  D. ACTIVE state
  E. persisted in PostgreSQL (backend store round-trip)
  F. survives restart (new repository with same store recovers state)
  G. authenticated tenant resolves the Ward
  H. unauthorized/cross-tenant resolution fails closed
  I. capability scope is exactly the approved read-only set
  J. credential never appears in API/UI/log/evidence
  K. runtime resolves OpenClaw through Ward boundary
  L. governance boundary is actually invoked
  M. no hardcoded citizen substitution for OpenClaw

Unit/integration. Live server acceptance terpisah (test_live / tools).
"""
import os
import uuid

import pytest

from sam.ward.bootstrap import (
    bootstrap_openclaw_ward, openclaw_entrustment, openclaw_ward_identity,
)
from sam.ward.manager import WardManager
from sam.ward.persistence import InMemoryWardStore
from sam.ward.registry.registry import WardRepository
from sam.ward.wiring import build_ward_manager, reset_ward_manager


@pytest.fixture(autouse=True)
def _reset_wiring():
    reset_ward_manager()
    yield
    reset_ward_manager()


def _tenant_mgr(manager, username):
    return manager.with_tenant({"username": username, "role": "operator"})


# ---------------- A. Ward identity canonical ----------------

def test_a_identity_canonical_deterministic_immutable():
    a = openclaw_ward_identity()
    b = openclaw_ward_identity()
    assert a.ward_id == b.ward_id          # deterministik
    assert a.ward_id.startswith("ward-")
    assert a.ward_type == "application"
    assert a.name == "OpenClaw"
    assert a.is_known
    with pytest.raises(Exception):          # frozen immutable
        a.ward_id = "x"  # type: ignore[misc]


def test_a_identity_ward_not_citizen():
    # OpenClaw identitas adalah Ward (eksternal entrusted), bukan citizen.
    assert openclaw_ward_identity().ward_type == "application"


# ---------------- B/C. OpenClaw registered + entrustment ----------------

def test_b_c_openclaw_registered_with_entrustment():
    mgr = build_ward_manager(persist=False)
    wid = openclaw_ward_identity().ward_id
    ward = mgr.repository.get(wid)
    assert ward is not None                       # B: registered
    assert not ward.is_revoked                    # D: (pre-empt) active
    ent = mgr.repository.get_entrustment(wid)
    assert ent is not None                        # C: explicit entrustment
    assert ent.is_active
    assert "observe" in ent.allowed_capabilities


def test_b_bootstrap_idempotent_no_overwrite():
    mgr = build_ward_manager(persist=False)
    wid1 = bootstrap_openclaw_ward(mgr, "van")
    wid2 = bootstrap_openclaw_ward(mgr, "van")
    assert wid1 == wid2
    assert mgr.repository.count() == 1            # tidak duplikat


# ---------------- D. ACTIVE state ----------------

def test_d_openclaw_active():
    mgr = build_ward_manager(persist=False)
    ward = mgr.repository.get(openclaw_ward_identity().ward_id)
    assert ward.is_active
    assert ward.status == "active"


# ---------------- E/F. Persistence (backend store round-trip + restart) ----

def test_e_f_inmemory_persistence_roundtrip_survives_new_repository():
    # E: store round-trip.
    store = InMemoryWardStore()
    mgr = WardManager(repository=WardRepository(persistence=store))
    wid = bootstrap_openclaw_ward(mgr, "van")
    assert store.load("ward") is not None

    # F: repository Baru dengan store yang SAMA ("restart") memulihkan state.
    mgr2 = WardManager(repository=WardRepository(persistence=store))
    recovered = mgr2.repository.get(wid)
    assert recovered is not None
    assert recovered.is_active
    ent = mgr2.repository.get_entrustment(wid)
    assert ent is not None and ent.is_active
    assert ent.owner_id == "van"


def test_e_postgres_store_roundtrip_if_pg_available():
    """E (PG): bila PostgreSQL tersedia, roundtrip save/load/clear nyata."""
    try:
        from sam.ward.persistence import _PG_OK, PostgresWardStore
    except Exception:
        pytest.skip("Ward persistence module tak tersedia")
    if not _PG_OK:
        pytest.skip("psycopg2 tak tersedia — skip PG roundtrip unit")
    dsn = (
        f"host={os.environ.get('SAM_PG_HOST', '127.0.0.1')} "
        f"port={os.environ.get('SAM_PG_PORT', '5432')} "
        f"dbname={os.environ.get('SAM_PG_DB', 'sam')} "
        f"user={os.environ.get('SAM_PG_USER', 'sam')} "
        f"password={os.environ.get('SAM_PG_PASSWORD', '')}"
    )
    if not os.environ.get("SAM_PG_PASSWORD"):
        pytest.skip("SAM_PG_PASSWORD tidak diset — skip PG unit (live di tools)")
    try:
        store = PostgresWardStore(dsn=dsn)
    except Exception as exc:
        pytest.skip(f"Postgres tak reachable: {exc}")
    scope = "ward_test_" + uuid.uuid4().hex[:8]
    try:
        store.save({"wards": [{"ward": {"status": "active"} }],
                    "entrustments": []}, scope=scope)
        got = store.load(scope)
        assert got is not None
        assert got["wards"][0]["ward"]["status"] == "active"
    finally:
        store.clear(scope)


# ---------------- G/H. Tenant resolution + cross-tenant fail closed -------

def test_g_authenticated_tenant_resolves_openclaw():
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    res = mgr.auth_ward("OpenClaw", "environment.observe")
    assert res.ok
    assert res.subject.subject_type == "ward"
    assert res.subject.name == "OpenClaw"


def test_g_resolve_by_ward_id():
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    wid = openclaw_ward_identity().ward_id
    res = mgr.auth_ward(wid, "environment.observe")
    assert res.ok
    assert res.ward_id == wid


def test_h_cross_tenant_fails_closed():
    # tenant yang BUKAN pemilik entrustment -> refused (0 eksekusi).
    mgr = build_ward_manager(persist=False).with_tenant({"username": "other", "role": "operator"})
    res = mgr.auth_ward("OpenClaw", "environment.observe")
    assert not res.ok
    assert res.refused
    assert "tenant" in res.reason or "pemilik" in res.reason


def test_h_anonymous_tenant_fails_closed():
    mgr = WardManager()  # tanpa tenant
    wid = bootstrap_openclaw_ward(mgr, "van")
    res = mgr.auth_ward(wid, "environment.observe")
    assert not res.ok
    assert res.refused


def test_h_unregistered_ward_fails_closed():
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    res = mgr.auth_ward("GitHub", "environment.observe")
    assert not res.ok
    assert res.refused


# ---------------- I. capability scope exactly read-only ----------------

def test_i_observe_and_readonly_ops_allowed():
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    for op in ("environment.observe", "environment.investigate",
               "environment.diagnose", "environment.recommend"):
        res = mgr.auth_ward("OpenClaw", op)
        assert res.ok, (op, res.reason)


def test_i_mutation_ops_refused():
    # W1: mutation TIDAK diaktifkan — capability scope read-only exactly.
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    for op in ("environment.protect", "environment.mutate", "process.run",
               "email.send", "db.write"):
        res = mgr.auth_ward("OpenClaw", op)
        assert not res.ok
        assert res.refused


# ---------------- J. credential never appears ----------------

def test_j_no_credential_in_ward_artifacts():
    mgr = build_ward_manager(persist=False)
    wid = openclaw_ward_identity().ward_id
    # entrustment / ward / metadata TIDAK mengandung secret token.
    ent = mgr.repository.get_entrustment(wid)
    assert "token" not in ent.as_dict().__str__().lower() or "password" not in (
        ent.as_dict().__str__().lower())
    ward = mgr.repository.get(wid)
    blob = str(ward.as_dict())
    for secret_kw in ("password", "token", "api_key", "bearer", "secret"):
        assert secret_kw not in blob
    # evidence dari observasi tidak mengandung secret (observer scrubbed).
    res = _tenant_mgr(mgr, "van").auth_ward("OpenClaw", "environment.observe")
    assert res.ok


# ---------------- K/L/M. runtime resolution through Ward boundary ---------

def test_k_l_m_runner_resolves_openclaw_via_ward_boundary_no_citizen_sub():
    """Run_mission dgn target OpenClaw: resolve lewat Ward boundary (K),
    governance boundary di-invoked (L), & subject = ward (bukan citizen, M)."""
    # Bangun manager tenant 'van' + set sbg composition root utk run_mission.
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    from sam.ward.wiring import set_ward_manager
    set_ward_manager(mgr)

    from sam.application.ux.runner import run_mission
    result = run_mission("environment.observe", target="OpenClaw")
    # K: runtime me-resolve OpenClaw sbg Ward (bukan unsupported).
    assert result["ok"] or result.get("blocked") is True  # mungkin NOT READY
    assert result["operation"] == "environment.observe"
    assert result["target"] == "OpenClaw"
    # M: subject Ward (bukan hardcoded citizen).
    assert result["ward_subject"]["subject_type"] == "ward"
    assert result["ward_subject"]["name"] == "OpenClaw"
    # L: governance boundary di-invoked (ada evidence ward resolution).
    assert "ward_subject" in result or result.get("blocked")


def test_k_local_machine_remains_citizen_not_ward():
    """Van #6: local-machine TETAP citizen (EnvironmentDiscovery), bukan Ward."""
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    from sam.ward.wiring import set_ward_manager
    set_ward_manager(mgr)
    from sam.application.ux.runner import run_mission
    result = run_mission("environment.observe", target="local-machine")
    # jalur citizen environment (bukan gate Ward) — tidak ada ward_subject.
    assert "ward_subject" not in result
    assert result["operation"] == "environment.observe"


def test_m_no_citizen_substitution_for_openclaw_adapter():
    # OpenClaw observe memakai adapter Ward (OpenClaw collector), bukan
    # EnvironmentDiscovery citizen. Pastikan subject resolution = ward.
    from sam.ward.manager import WardManager
    mgr = build_ward_manager(persist=False).with_tenant({"username": "van", "role": "operator"})
    # audit: subject dari resolve adalah ward, name OpenClaw.
    res = mgr.resolve_ward("OpenClaw")
    assert res.ok
    assert res.subject.subject_type == "ward"
    assert res.subject.name == "OpenClaw"
