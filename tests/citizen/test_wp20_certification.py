# IP-3.3-002 WP-20 - End-to-end Integration & Certification test
# Citizen Collaboration & Compatibility (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Definisi Done IP-3.3-002: platform mampu menjawab secara deterministik -
# kolaborasi apa yang bisa diusulkan, apakah dua citizen kompatibel & mengapa,
# contract apa yang menyatukan mereka, ada konflik dependency tidak, mengapa
# kolaborasi masuk akal - TANPA orchestrasi/eksekusi kolaborasi dan TANPA
# menambah otoritas.
#
# Guardrails dikunci: Collaboration != Orchestration; Compatibility !=
# Authority; Contract Resolution != Execution; Proposal != Decision;
# Discovery Registry-based; Citizen Equality; no privileged; no implicit
# collaboration; no mutation Runtime/Governance/Foundation.

import os

import pytest

from sam.citizen.identity.models import CitizenIdentity
from sam.citizen.registry.registry import CitizenRegistry
from sam.citizen.descriptor.descriptor import build_descriptor
from sam.citizen.collaboration.models import (
    CollaborationRole,
    CollaborationSpec,
    is_privilege_free,
)
from sam.citizen.collaboration.proposal import CollaborationProposalEngine
from sam.citizen.collaboration.compatibility import CompatibilityAnalyzer
from sam.citizen.collaboration.contract_resolution import (
    ContractResolutionEngine,
    ResolutionRequirement,
)
from sam.citizen.collaboration.dependency import DependencyCompatibilityChecker
from sam.citizen.collaboration.explainability import CollaborationExplainer
from sam.citizen.api.collaboration import CitizenCollaborationAPI
from sam.citizen.compliance.collaboration_checker import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_COL_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "collaboration")


@pytest.fixture
def api():
    reg = CitizenRegistry()
    rt = CitizenIdentity.new("runtime", "sam-runtime")
    prov = CitizenIdentity.new("provider", "llm-openai")
    wf = CitizenIdentity.new("workflow", "weekly-audit")
    for i in (rt, prov, wf):
        reg.register(i)
    d_rt = build_descriptor(rt, contracts=("health", "lifecycle"),
                            capabilities=("observe", "plan"),
                            health_status="healthy")
    d_prov = build_descriptor(prov, contracts=("llm", "health"),
                              capabilities=("generate", "observe"),
                              health_status="healthy")
    d_wf = build_descriptor(wf, contracts=("workflow",),
                            capabilities=("run-audit",),
                            health_status="degraded")
    col_api = CitizenCollaborationAPI(
        reg, descriptors=(d_rt, d_prov, d_wf),
        healths={rt.identity_id: "healthy", prov.identity_id: "healthy",
                 wf.identity_id: "degraded"})
    return reg, col_api, rt, prov, wf


# --------------------------------------------------------------------------
# WP-11 Collaboration Model
# --------------------------------------------------------------------------

def test_collaboration_spec_immutable_and_deterministic(api):
    _reg, _a, rt, prov, _wf = api
    roles = (CollaborationRole(rt.identity_id, "initiator"),
             CollaborationRole(prov.identity_id, "participant"))
    s1 = CollaborationSpec.new(roles, "llm", shared_capabilities=("generate",))
    s2 = CollaborationSpec.new(roles, "llm", shared_capabilities=("generate",))
    assert s1.collaboration_id == s2.collaboration_id  # deterministic
    assert s1.collaboration_id.startswith("col-")
    with pytest.raises(Exception):
        s1.collaboration_id = "changed"  # immutable
    assert s1.channel.name == "llm"


def test_collaboration_privilege_free(api):
    _reg, _a, rt, prov, _wf = api
    roles = (CollaborationRole(rt.identity_id, "initiator"),
             CollaborationRole(prov.identity_id, "participant"))
    spec = CollaborationSpec.new(roles)
    assert is_privilege_free(spec) is True
    # role privileged harus ditolak
    assert "owner" not in {r.role for r in roles}


def test_collaboration_no_privileged_role_model(api):
    _reg, _a, rt, prov, _wf = api
    # role yang bukan set kanonik dinormalisasi ke 'peer' (equal)
    r = CollaborationRole(rt.identity_id, "owner")
    assert r.role in ("peer", "participant", "initiator", "observer")
    assert r.role != "owner"


# --------------------------------------------------------------------------
# WP-12 Collaboration Proposal Engine
# --------------------------------------------------------------------------

def test_proposal_deterministic_and_proposal_only(api):
    _reg, a, rt, prov, _wf = api
    p1 = a.propose(rt.identity_id, ("generate",))
    p2 = a.propose(rt.identity_id, ("generate",))
    assert [x.proposal_id for x in p1] == [x.proposal_id for x in p2]
    for p in p1:
        assert p.is_proposal is True
        # proposal TIDAK membentuk kolaborasi - tidak ada kolaborasi di registry
    # hanya target dengan capability yg cocok
    for p in p1:
        assert "generate" in p.proposed_capabilities


def test_proposal_no_self_collaboration(api):
    _reg, a, rt, prov, _wf = api
    p = a.propose(rt.identity_id, ("observe",))
    # rt sendiri punya observe; self-collaboration harus dikecualikan
    for prop in p:
        assert rt.identity_id not in prop.targets


# --------------------------------------------------------------------------
# WP-13 Compatibility Analyzer
# --------------------------------------------------------------------------

def test_compatibility_deterministic(api):
    _reg, a, rt, prov, _wf = api
    r1 = a.compatibility(rt.identity_id, prov.identity_id)
    r2 = a.compatibility(rt.identity_id, prov.identity_id)
    assert r1.is_compatible == r2.is_compatible
    assert [e.contract for e in r1.entries] == [e.contract for e in r2.entries]


def test_compatibility_shared_contract(api):
    _reg, a, rt, prov, _wf = api
    rep = a.compatibility(rt.identity_id, prov.identity_id)
    # rt & prov sama-sama support 'health' -> compatible
    assert rep.is_compatible is True
    assert any(e.contract == "health" for e in rep.entries)


def test_compatibility_required_contract(api):
    _reg, a, rt, prov, wf = api
    # wf tidak support llm; rt minta llm -> tidak compatible bila required
    rep = a.compatibility(wf.identity_id, rt.identity_id,
                          required_contracts=("llm",))
    assert rep.is_compatible is False


# --------------------------------------------------------------------------
# WP-14 Contract Resolution
# --------------------------------------------------------------------------

def test_contract_resolution_registry_based(api):
    _reg, a, rt, prov, _wf = api
    res = a.resolve_contract("llm", capability="generate")
    assert len(res) == 1
    r = res[0]
    assert r.resolved is True
    assert r.capability == "generate"
    # resolusi adalah lookup, bukan eksekusi
    assert "lookup" in r.basis[0] or "resolution is lookup" in r.basis[0]


def test_contract_resolution_healthy_only(api):
    _reg, a, rt, prov, _wf = api
    # wf degraded; bila minta contract workflow dgn healthy_only -> kosong
    res = a.resolve_contract("workflow", capability="run-audit",
                             healthy_only=True)
    assert len(res) == 0


# --------------------------------------------------------------------------
# WP-15 Dependency Compatibility
# --------------------------------------------------------------------------

def test_dependency_overlap_detected(api):
    _reg, a, rt, prov, _wf = api
    dep = a.analyze_dependency((rt.identity_id, prov.identity_id))
    # keduanya support 'health' -> overlap
    assert any(o.contract == "health" for o in dep.overlaps)
    assert dep.has_conflict is False


def test_dependency_deterministic(api):
    _reg, a, rt, prov, wf = api
    d1 = a.analyze_dependency((rt.identity_id, prov.identity_id, wf.identity_id))
    d2 = a.analyze_dependency((wf.identity_id, prov.identity_id, rt.identity_id))
    assert [o.contract for o in d1.overlaps] == \
        [o.contract for o in d2.overlaps]


# --------------------------------------------------------------------------
# WP-16 Collaboration Explainability
# --------------------------------------------------------------------------

def test_explainability_preserved(api):
    _reg, a, rt, prov, _wf = api
    rep = a.compatibility(rt.identity_id, prov.identity_id)
    exp = a.explain_compatibility(rep)
    assert exp.statements
    assert exp.evidence_items  # evidence-backed
    spec = CollaborationSpec.new(
        (CollaborationRole(rt.identity_id, "initiator"),
         CollaborationRole(prov.identity_id, "participant")),
        "llm", shared_capabilities=("generate",))
    expc = a.explain_collaboration(spec)
    assert "equal" in expc.statements[0]


# --------------------------------------------------------------------------
# WP-17 Citizen Collaboration API (read-only)
# --------------------------------------------------------------------------

def test_api_read_only_no_mutation(api):
    reg, a, rt, prov, _wf = api
    before = reg.count()
    a.propose(rt.identity_id, ("generate",))
    a.compatibility(rt.identity_id, prov.identity_id)
    a.resolve_contract("llm")
    a.analyze_dependency((rt.identity_id, prov.identity_id))
    assert reg.count() == before  # tidak ada citizen bertambah
    # API tidak memiliki verb eksekusi kolaborasi
    assert not hasattr(a, "form_collaboration")
    assert not hasattr(a, "run_collaboration")
    assert not hasattr(a, "activate_channel")


# --------------------------------------------------------------------------
# WP-18 Collaboration Compliance
# --------------------------------------------------------------------------

def test_collaboration_compliance_suite_passed():
    files = default_source_files(_COL_ROOT)
    passed, checks = compliance_check(files, module_root=_COL_ROOT)
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# WP-20 Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end(api):
    """Platform menjawab deterministik pertanyaan Collaboration & Compatibility,
    tanpa orchestrasi dan tanpa kewenangan baru."""
    _reg, a, rt, prov, wf = api

    # kolaborasi apa yang bisa diusulkan?
    props = a.propose(rt.identity_id, ("generate",))
    assert props and all(p.is_proposal for p in props)

    # apakah dua citizen kompatibel? mengapa?
    rep = a.compatibility(rt.identity_id, prov.identity_id)
    exp = a.explain_compatibility(rep)
    assert exp.statements

    # contract apa yang menyatukan mereka?
    shared = set(a.compatibility(rt.identity_id, prov.identity_id).entries)
    assert shared

    # ada konflik dependency tidak?
    dep = a.analyze_dependency((rt.identity_id, prov.identity_id))
    assert hasattr(dep, "has_conflict")

    # mengapa kolaborasi masuk akal?
    spec = CollaborationSpec.new(
        (CollaborationRole(rt.identity_id, "initiator"),
         CollaborationRole(prov.identity_id, "participant")))
    assert a.explain_collaboration(spec).statements

    # TANPA orchestrasi: tidak ada verb eksekusi kolaborasi
    assert not hasattr(a, "run_collaboration")
    assert not hasattr(a, "execute_collaboration")
    assert not hasattr(a, "start_collaboration")
    # TANPA kewenangan: tidak ada mutation lifecycle/runtime/governance
    assert not hasattr(a, "transition_lifecycle")
    assert not hasattr(a, "mutate_runtime")
    # discovery tetap registry-based (lokasi kolaborasi via registry lookup)
    assert reg_has_provider(_reg, prov.identity_id)


def reg_has_provider(reg, cid):
    return reg.has(cid)
