# IP-3.3-001 WP-10 - End-to-end Integration & Certification test
# Citizen Foundation (AO-3.3-001 / ED-3.3-001)
#
# Definisi Done IP-3.3-001: platform mampu menjawab secara deterministik -
# citizen apa tersedia, capability apa dimiliki, status kesehatan, lifecycle,
# cara ditemukan, kontrak didukung, compliant atau tidak, mengapa valid -
# TANPA mekanisme kolaborasi antar-citizen (belum federation).
#
# Prinsip kunci:
#   Citizen Equality  - runtime/provider/workflow/mission semua setara.
#   Registry != Authority - registry hanya simpan/discovery/metadata.
#   Citizen != Runtime - model citizen mendahului & tidak bergantung runtime.

import os

import pytest

from sam.citizen.identity.models import CitizenIdentity
from sam.citizen.registry.registry import CitizenRegistry, RegistryConflictError
from sam.citizen.descriptor.descriptor import build_descriptor, CitizenDescriptor
from sam.citizen.capability.models import CitizenCapability
from sam.citizen.discovery.engine import (
    CitizenDiscoveryEngine,
    DiscoveryQuery,
)
from sam.citizen.health.models import CitizenHealth, CitizenHealthAnalyzer
from sam.citizen.lifecycle.models import CitizenLifecycle, CitizenLifecycleAnalyzer
from sam.citizen.api.citizen import CitizenAPI
from sam.citizen.compliance.checker import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CIT_ROOT = os.path.join(_ROOT, "src", "sam", "citizen")


def _seed() -> tuple:
    """Register 3 citizen (runtime/provider/workflow) + descriptor + api."""
    reg = CitizenRegistry()
    rt = CitizenIdentity.new("runtime", "sam-runtime", version="1.0")
    prov = CitizenIdentity.new("provider", "llm-openai", version="2.1")
    wf = CitizenIdentity.new("workflow", "weekly-audit", version="0.9")
    reg.register(rt, registered_at="t0")
    reg.register(prov, registered_at="t0")
    reg.register(wf, registered_at="t0")

    d_rt = build_descriptor(rt, contracts=("health", "lifecycle"),
                            capabilities=("observe", "plan"),
                            health_status="healthy")
    d_prov = build_descriptor(prov, contracts=("llm", "health"),
                              capabilities=("generate", "observe"),
                              health_status="healthy")
    d_wf = build_descriptor(wf, contracts=("workflow",),
                            capabilities=("run-audit",),
                            health_status="degraded")
    healths = {
        rt.identity_id: CitizenHealth(rt.identity_id, "healthy"),
        prov.identity_id: CitizenHealth(prov.identity_id, "healthy"),
        wf.identity_id: CitizenHealth(wf.identity_id, "degraded"),
    }
    lifecycles = {
        rt.identity_id: CitizenLifecycle(rt.identity_id, "active"),
        prov.identity_id: CitizenLifecycle(prov.identity_id, "active"),
        wf.identity_id: CitizenLifecycle(wf.identity_id, "discovered"),
    }
    api = CitizenAPI(reg, descriptors={
        rt.identity_id: d_rt, prov.identity_id: d_prov, wf.identity_id: d_wf},
        healths=healths, lifecycles=lifecycles)
    return reg, api, rt, prov, wf


# --------------------------------------------------------------------------
# 1. Citizen Identity Model (WP-01)
# --------------------------------------------------------------------------

def test_identity_immutable():
    i = CitizenIdentity.new("provider", "llm-openai", version="1.0")
    with pytest.raises(Exception):
        i.identity_id = "changed"


def test_identity_deterministic_id():
    a = CitizenIdentity.new("runtime", "sam", version="1.0", namespace="prod")
    b = CitizenIdentity.new("runtime", "sam", version="1.0", namespace="prod")
    assert a.identity_id == b.identity_id
    assert a.identity_id.startswith("cit-")


def test_identity_equal_kinds():
    rt = CitizenIdentity.new("runtime", "sam-runtime")
    prov = CitizenIdentity.new("provider", "llm")
    # keduanya citizen; tidak ada perlakuan istimewa pada runtime
    assert rt.kind == "runtime"
    assert prov.kind == "provider"
    assert rt.matches_kind("RUNTIME")  # case-insensitive, equal


# --------------------------------------------------------------------------
# 2. Citizen Registry (WP-02)
# --------------------------------------------------------------------------

def test_registry_unique_identity():
    reg = CitizenRegistry()
    i = CitizenIdentity.new("provider", "dup", version="1.0")
    reg.register(i)
    with pytest.raises(RegistryConflictError):
        reg.register(CitizenIdentity.new("provider", "dup", version="1.0"))


def test_registry_indexed_query():
    reg, _api, rt, prov, wf = _seed()
    assert reg.count() == 3
    assert set(reg.kinds()) == {"provider", "runtime", "workflow"}
    assert [e.name for e in reg.by_kind("runtime")] == ["sam-runtime"]
    assert reg.has(rt.identity_id)


def test_registry_unregister():
    reg, _api, rt, prov, wf = _seed()
    assert reg.unregister(prov.identity_id) is True
    assert reg.count() == 2
    assert reg.get(prov.identity_id) is None


# --------------------------------------------------------------------------
# 3. Citizen Descriptor (WP-03)
# --------------------------------------------------------------------------

def test_descriptor_completeness():
    i = CitizenIdentity.new("service", "svc-a", version="1.0")
    d = build_descriptor(i, contracts=("health",))
    assert d.is_complete() is True
    assert d.supports_contract("health")
    assert d.basis  # explainable metadata


def test_descriptor_contract_driven():
    _reg, api, rt, prov, _wf = _seed()
    assert api.contracts_of(prov.identity_id) == ("llm", "health")
    assert api.descriptor_of(rt.identity_id).has_capability("observe")


# --------------------------------------------------------------------------
# 4. Citizen Capability Model (WP-04)
# --------------------------------------------------------------------------

def test_capability_contract():
    cap = CitizenCapability.new("generate", owner_identity_id="x",
                                output_schema="text", side_effects=())
    assert cap.capability_id.startswith("cap-")
    assert cap.contract.is_read_only is True


def test_capability_stable_id():
    a = CitizenCapability.new("observe", owner_identity_id="o", version="1.0")
    b = CitizenCapability.new("observe", owner_identity_id="o", version="1.0")
    assert a.capability_id == b.capability_id


# --------------------------------------------------------------------------
# 5. Citizen Discovery Engine (WP-05)
# --------------------------------------------------------------------------

def test_discovery_deterministic():
    reg, _api, rt, prov, wf = _seed()
    eng = CitizenDiscoveryEngine(reg)
    q = DiscoveryQuery(kind="runtime")
    r1 = eng.discover(q)
    r2 = eng.discover(q)
    assert [e.identity_id for e in r1.matches] == \
        [e.identity_id for e in r2.matches]
    assert r1.count() == 1


def test_discovery_contract_driven():
    reg, _api, rt, prov, wf = _seed()
    eng = CitizenDiscoveryEngine(reg)
    eng.attach_descriptors((build_descriptor(rt, contracts=("health","lifecycle"),
                                             capabilities=("observe","plan"),
                                             health_status="healthy"),
                            build_descriptor(prov, contracts=("llm","health"),
                                             capabilities=("generate","observe"),
                                             health_status="healthy"),
                            build_descriptor(wf, contracts=("workflow",),
                                             capabilities=("run-audit",),
                                             health_status="degraded")))
    r = eng.discover(DiscoveryQuery(contract="llm"))
    assert [e.name for e in r.matches] == ["llm-openai"]
    r2 = eng.discover(DiscoveryQuery(capability="observe"))
    assert set(e.name for e in r2.matches) == {"sam-runtime", "llm-openai"}


def test_discovery_no_implicit():
    reg, _api, rt, prov, wf = _seed()
    eng = CitizenDiscoveryEngine(reg)
    with pytest.raises(ValueError):
        eng.discover(DiscoveryQuery())


# --------------------------------------------------------------------------
# 6. Citizen Health Model (WP-06)
# --------------------------------------------------------------------------

def test_health_deterministic_level():
    an = CitizenHealthAnalyzer()
    assert an.analyze("x", ("healthy", "healthy")).level == "healthy"
    assert an.analyze("x", ("healthy", "degraded")).level == "degraded"
    assert an.analyze("x", ("healthy", "unavailable")).level == "unavailable"
    assert an.analyze("x", ()).level == "unknown"


def test_health_is_observation_not_decision():
    h = CitizenHealthAnalyzer().analyze("rt-a", ("unavailable",))
    assert h.is_available is False
    # health hanya status, tidak men-trigger restart/aktifasi
    assert h.level == "unavailable"


# --------------------------------------------------------------------------
# 7. Citizen Lifecycle Model (WP-07)
# --------------------------------------------------------------------------

def test_lifecycle_consistency():
    lc = CitizenLifecycle(identity_id="x", stage="registered")
    an = CitizenLifecycleAnalyzer()
    assert an.can_transition("registered", "discovered") is True
    assert an.can_transition("registered", "active") is False  # harus lewat discovered
    assert an.is_consistent(lc) is True


def test_lifecycle_proposal_not_mutation():
    lc = CitizenLifecycle(identity_id="x", stage="discovered")
    an = CitizenLifecycleAnalyzer()
    ok, why = an.propose_transition(lc, "active")
    assert ok is True
    # proposal, bukan mutation - transisi TIDAK diterapkan
    assert lc.stage == "discovered"
    assert "requires authorized actor" in why


# --------------------------------------------------------------------------
# 8. Citizen API (WP-08)
# --------------------------------------------------------------------------

def test_api_read_only_answers_questions():
    _reg, api, rt, prov, wf = _seed()
    # citizen apa tersedia? capability? kesehatan? lifecycle? kontrak?
    assert api.count == 3
    assert set(api.kinds()) == {"provider", "runtime", "workflow"}
    assert "observe" in api.capabilities_of(rt.identity_id)
    assert api.health_of(wf.identity_id) == "degraded"
    assert api.lifecycle_of(prov.identity_id) == "active"
    assert api.contracts_of(prov.identity_id) == ("llm", "health")


def test_api_never_mutates():
    reg, _api, rt, prov, wf = _seed()
    api = _api
    before = api.count
    api.all()
    api.discover(kind="runtime")
    api.get(rt.identity_id)
    api.validity(rt.identity_id)
    # read-only: tidak ada citizen bertambah/hilang
    assert api.count == before
    assert reg.count() == 3


def test_api_validity_explainable():
    _reg, api, rt, prov, wf = _seed()
    valid, basis = api.validity(rt.identity_id)
    assert valid is True
    assert "identity immutable" in basis


# --------------------------------------------------------------------------
# 9. Compliance suite (WP-09)
# --------------------------------------------------------------------------

def test_citizen_compliance_suite_passed():
    files = [f for f in default_source_files(_CIT_ROOT) if "checker.py" not in f]
    passed, checks = compliance_check(files, module_root=_CIT_ROOT,
                                      implementation_dirs=())
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# 10. Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end():
    """Platform menjawab deterministik 8 pertanyaan Citizen Foundation, tanpa
    kolaborasi antar-citizen dan tanpa kewenangan baru."""
    reg, api, rt, prov, wf = _seed()

    # citizen apa saja yang tersedia?
    assert api.count >= 3
    # capability apa yang dimiliki setiap citizen?
    assert api.capabilities_of(rt.identity_id)
    assert api.capabilities_of(prov.identity_id)
    # apa status kesehatannya?
    assert api.health_of(rt.identity_id) in ("healthy", "degraded",
                                             "unavailable", "unknown")
    # apa lifecycle-nya?
    assert api.lifecycle_of(prov.identity_id) in (
        "declared", "registered", "discovered", "active", "retired")
    # bagaimana citizen ditemukan? (contract-driven lookup)
    found = api.discover(contract="llm")
    assert found.count() >= 1
    # apa kontrak yang didukung?
    assert api.contracts_of(prov.identity_id)
    # apakah citizen compliant? (checker lulus)
    files = [f for f in default_source_files(_CIT_ROOT) if "checker.py" not in f]
    passed, _checks = compliance_check(files, module_root=_CIT_ROOT,
                                       implementation_dirs=())
    assert passed
    # mengapa citizen dianggap valid? (basis explainable)
    valid, basis = api.validity(rt.identity_id)
    assert valid is True
    assert basis

    # TANPA kolaborasi antar-citizen: registry hanya metadata, no federation
    assert hasattr(api, "discover")  # discovery ya
    # no authority: API tidak punya aktivat/deaktivat/mutasi lifecycle
    assert not hasattr(api, "activate_citizen")
    assert not hasattr(api, "deactivate_citizen")
    assert not hasattr(api, "transition_lifecycle")
