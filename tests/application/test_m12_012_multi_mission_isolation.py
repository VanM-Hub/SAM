"""test_m12_012_multi_mission_isolation.py — M12-012 Multi-Mission Isolation.

Kontrak M12-012: State keyed per tenant/user + mission + execution. Tanpa
global `self._state`/`self._request`/`self._audit` authority.
  - MissionRegistry: operasi selalu via key (tenant, mission_id, execution_id);
    tanpa mission_id -> ValueError (bukan state global); get lintas mission
    tidak bocor; get key tak dikenal -> None.
  - MultiMissionService: tiap mission = instance OTONOM ter-isolasi; operasi
    selalu via key eksplisit; cross-tenant / mission tak dikenal -> KeyError.
  - Isolasi cross-tenant: access mission milik tenant lain -> DENIED.

Test memakai stub service (tanpa AI) agar cepat & deterministik; isolasi state
yang diuji ada di registry/adapter, bukan di AI.
"""
from __future__ import annotations

import pytest

from sam.application.ux.mission_registry import (
    MissionRegistry,
    MultiMissionService,
    make_mission_id,
)


# ---------- MissionRegistry: keying + isolasi ----------

def test_registry_save_get_per_key():
    r = MissionRegistry()
    r.save("van", "m1", "x1", {"status": "A"})
    assert r.get("van", "m1", "x1") == {"status": "A"}
    # mission berbeda tidak bocor
    assert r.get("van", "m2", "x1") is None
    # execution berbeda tidak bocor
    assert r.get("van", "m1", "x2") is None


def test_registry_no_global_without_mission_id():
    r = MissionRegistry()
    r.save("van", "m1", "x1", {"v": 1})
    # tanpa mission_id -> error (bukan "current state" global)
    with pytest.raises(ValueError):
        r.get("van", "", "x1")


def test_registry_cross_tenant_isolated():
    r = MissionRegistry()
    r.save("alice", "m1", "x1", {"owner": "alice"})
    r.save("bob", "m1", "x1", {"owner": "bob"})
    # mission_id sama, tenant beda -> terpisah
    assert r.get("alice", "m1", "x1") == {"owner": "alice"}
    assert r.get("bob", "m1", "x1") == {"owner": "bob"}
    # list_keys filter tenant
    keys = r.list_keys(tenant="alice")
    assert all(k["tenant"] == "alice" for k in keys)
    assert len(keys) == 1


def test_registry_delete_scope():
    r = MissionRegistry()
    r.save("t", "m1", "x1", 1)
    r.save("t", "m1", "x2", 2)
    assert r.delete("t", "m1", "x1") is True
    assert r.has("t", "m1", "x1") is False
    assert r.has("t", "m1", "x2") is True


# ---------- Stub service (tanpa AI) utk MultiMissionService ----------

class _StubMission:
    """MissionUXService tiruan: per-instance jadi request_id unik, state dasar."""

    def __init__(self, tag: str) -> None:
        self.tag = tag
        self._request_id = f"req-{tag}"

    def submit(self, text, idempotency_key=None):
        return _StubState(self._request_id, {"mission_id": f"mission-{self.tag}", "st": "waiting"})

    def decide(self, intent, approver="user"):
        return _StubState(self._request_id, {"mission_id": f"mission-{self.tag}", "st": "done"})


class _StubState:
    def __init__(self, request_id, observability) -> None:
        self.request_id = request_id
        self.observability = observability

    def as_dict(self):
        return {
            "request_id": self.request_id,
            "observability": dict(self.observability),
            "status": self.observability.get("st"),
        }


# ---------- MultiMissionService: isolasi antar mission / tenant ----------

def test_multimission_two_missions_isolated():
    counter = {"n": 0}

    def factory():
        counter["n"] += 1
        return _StubMission(f"svc{counter['n']}")

    mms = MultiMissionService(service_factory=factory)
    a = mms.create("van", "mission-A")
    b = mms.create("van", "mission-B")
    sa = mms.submit("van", "mission-A", "misi A")
    sb = mms.submit("van", "mission-B", "misi B")
    # request_id mission A beda dari mission B -> state terisolasi (bukan global)
    assert sa["request_id"] != sb["request_id"]
    # snapshot disimpan per execution (key eksplisit, bukan state global)
    ex_a = sa["observability"]["mission_id"]
    ex_b = sb["observability"]["mission_id"]
    assert mms.get_state("van", "mission-A", ex_a) is not None
    assert mms.get_state("van", "mission-B", ex_b) is not None
    # lintas mission tetap terisolasi: state mission-B tidak ada di mission-A
    assert mms.get_state("van", "mission-A", ex_b) is None


def test_multimission_unknown_mission_denied():
    mms = MultiMissionService(service_factory=lambda: _StubMission("s"))
    mms.create("van", "m1")
    with pytest.raises(KeyError):
        mms.submit("van", "tidak-ada", "halo")


def test_multimission_cross_tenant_denied():
    mms = MultiMissionService(service_factory=lambda: _StubMission("s"))
    mms.create("alice", "m1")
    # bob mencoba akses mission milik alice -> cross-tenant DENIED
    with pytest.raises(KeyError) as exc:
        mms.submit("bob", "m1", "misi")
    assert "cross-tenant" in str(exc.value)


def test_multimission_no_global_state_default():
    mms = MultiMissionService(service_factory=lambda: _StubMission("s"))
    mms.create("van", "m1")
    # tidak ada anggota berupa state global tunggal di registry
    reg = mms.registry()
    keys = reg.list_keys()
    # setiap key harus punya mission_id eksplisit
    assert all(k["mission_id"] for k in keys)


def test_multimission_mission_count():
    mms = MultiMissionService(service_factory=lambda: _StubMission("s"))
    mms.create("van", "m1")
    mms.create("van", "m2")
    mms.create("alice", "m3")
    assert mms.mission_count() == 3


def test_make_mission_id_unique():
    a = make_mission_id()
    b = make_mission_id()
    assert a != b
    assert a.startswith("m_")
    assert b.startswith("m_")
