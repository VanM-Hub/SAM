"""Test wiring Citizen Ecosystem: registry ter-wire nyata + discovery jalan.

Menutup gap review: sebelumnya CitizenRegistry/CitizenAPI didefinisikan tapi
tidak pernah di-instantiate di composition root (0 import). Test ini membuktikan
registry kini ter-wire, berisi citizen NYATA, discovery deterministik, dan
API tetap read-only (Registry != Authority).
"""
from __future__ import annotations

import pytest

from sam.citizen.wiring import citizen_registry, citizen_api


def test_registry_is_wired_with_real_citizens():
    assert citizen_registry.count() > 0


def test_all_expected_kinds_registered():
    kinds = set(citizen_api.kinds())
    assert {"runtime", "provider", "workflow", "policy", "mission",
            "capability", "service"} <= kinds


def test_no_duplicate_identity():
    ids = [e.identity_id for e in citizen_registry.all()]
    assert len(ids) == len(set(ids))


def test_discover_by_kind_is_deterministic():
    r1 = citizen_api.discover(kind="runtime")
    r2 = citizen_api.discover(kind="runtime")
    assert [e.identity_id for e in r1.matches] == [e.identity_id for e in r2.matches]
    assert r1.count() >= 1


def test_discover_by_capability():
    r = citizen_api.discover(capability="execution.preview")
    assert r.count() >= 1


def test_discovery_requires_criteria():
    with pytest.raises(ValueError):
        citizen_api.discover()


def test_readonly_api_has_no_mutation():
    assert not hasattr(citizen_api, "register")
    assert not hasattr(citizen_api, "unregister")
    assert not hasattr(citizen_api, "activate")


def test_get_unknown_returns_none():
    assert citizen_api.get("cit-nonexistent") is None
