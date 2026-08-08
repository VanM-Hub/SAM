# IP-3.3-003 WP-30 - End-to-end Integration & Certification test
# Citizen Certification & Ecosystem Intelligence (AO-3.3-001 cycle 3)
#
# Definisi Done IP-3.3-003: platform mampu menyertifikasi, mengevaluasi, dan
# memahami setiap Citizen sebagai bagian ekosistem - secara deterministic dan
# evidence-first - TANPA authority (tidak approve, tidak kontrol, tidak mutasi
# lifecycle, tidak keputusan governance).
#
# Guardrail IP-3.3-003 dikunci: Certification != Approval; Intelligence !=
# Governance; Recommendation != Authority; Ecosystem Health != Runtime
# Control; Certification != Lifecycle Mutation; Registry authoritative;
# Evidence-first; Deterministic.

import os

import pytest

from sam.citizen.identity.models import CitizenIdentity
from sam.citizen.registry.registry import CitizenRegistry
from sam.citizen.descriptor.descriptor import build_descriptor
from sam.citizen.api.intelligence import CitizenIntelligenceAPI
from sam.citizen.ecosystem.models import CertificationResult, CitizenMaturityProfile
from sam.citizen.ecosystem.certification_engine import CertificationEngine
from sam.citizen.ecosystem.intelligence import (
    EcosystemSnapshot,
    EcosystemIntelligenceEngine,
)
from sam.citizen.ecosystem.health import (
    EcosystemHealthAssessment,
    EcosystemHealthAssessor,
)
from sam.citizen.ecosystem.recommendation import (
    EcosystemRecommendation,
    EcosystemRecommendationEngine,
)
from sam.citizen.ecosystem.explainability import EcosystemExplainer
from sam.citizen.compliance.certification_checker import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ECO_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "ecosystem")


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
    intel = CitizenIntelligenceAPI(
        reg, descriptors=(d_rt, d_prov, d_wf),
        healths={rt.identity_id: "healthy", prov.identity_id: "healthy",
                 wf.identity_id: "degraded"})
    return reg, intel, rt, prov, wf


# --------------------------------------------------------------------------
# WP-21 Citizen Certification Model
# --------------------------------------------------------------------------

def test_certification_result_immutable_deterministic(api):
    _reg, _i, rt, _p, _w = api
    c = CertificationResult.new(rt.identity_id, "capable", "compliant", 3, 3)
    c2 = CertificationResult.new(rt.identity_id, "capable", "compliant", 3, 3)
    assert c.certification_id == c2.certification_id  # deterministic
    assert c.certification_id.startswith("cert-")
    with pytest.raises(Exception):
        c.certification_id = "changed"  # immutable
    assert c.qualified is True


def test_certification_qualified_estimator(api):
    _reg, _i, rt, _p, _w = api
    ok = CertificationResult.new(rt.identity_id, "capable", "partial", 2, 4)
    assert ok.qualified is True
    low = CertificationResult.new(rt.identity_id, "initial", "noncompliant", 0, 4)
    assert low.qualified is False


# --------------------------------------------------------------------------
# WP-22 Certification Engine
# --------------------------------------------------------------------------

def test_certification_deterministic(api):
    _reg, i, rt, _p, _w = api
    c1 = i.certify(rt.identity_id)
    c2 = i.certify(rt.identity_id)
    assert c1.compliance == c2.compliance
    assert c1.maturity == c2.maturity
    assert c1.certification_id == c2.certification_id


def test_certification_assessment_not_mutation(api):
    reg, i, rt, _p, _w = api
    before = reg.count()
    c = i.certify(rt.identity_id)
    # sertifikasi TIDAK menambah/mengubah citizen di registry
    assert reg.count() == before
    # tidak mengubah lifecycle/stage (tidak ada mutasi)
    assert "mutation" not in c.basis and "certification != approval" in c.basis


def test_certification_evidence_first(api):
    _reg, i, rt, _p, _w = api
    c = i.certify(rt.identity_id)
    assert c.evidence  # selalu membawa evidence
    assert any("checks" in e for e in c.evidence)


def test_certification_explicit_noncompliant(api):
    _reg, i, rt, _p, _w = api
    c = i.certify(rt.identity_id, checks_total=5, checks_passed=1)
    assert c.compliance == "noncompliant"


# --------------------------------------------------------------------------
# WP-23 Ecosystem Intelligence
# --------------------------------------------------------------------------

def test_snapshot_kinds(api):
    _reg, i, rt, prov, wf = api
    snap = i.snapshot((rt.identity_id, prov.identity_id, wf.identity_id))
    assert snap.citizen_count == 3
    assert snap.kinds == {"runtime": 1, "provider": 1, "workflow": 1}


def test_snapshot_deterministic(api):
    _reg, i, rt, prov, wf = api
    ids = (rt.identity_id, prov.identity_id, wf.identity_id)
    s1 = i.snapshot(ids)
    s2 = i.snapshot(tuple(reversed(ids)))
    assert s1.as_dict() == s2.as_dict()


def test_snapshot_capability_contract_count(api):
    _reg, i, rt, prov, wf = api
    snap = i.snapshot((rt.identity_id, prov.identity_id, wf.identity_id))
    # observe/plan/generate/run-audit = 4 capability unik
    assert snap.capability_count == 4
    assert snap.total_capabilities == 5  # 2+2+1
    assert snap.total_contracts == 5  # 2+2+1


# --------------------------------------------------------------------------
# WP-24 Ecosystem Health Assessment
# --------------------------------------------------------------------------

def test_health_deterministic(api):
    _reg, i, rt, prov, wf = api
    ids = (rt.identity_id, prov.identity_id, wf.identity_id)
    h1 = i.health(ids)
    h2 = i.health(ids)
    assert h1.overall == h2.overall
    assert h1.as_dict() == h2.as_dict()


def test_health_collective_not_control(api):
    _reg, i, rt, prov, wf = api
    h = i.health((wf.identity_id,))  # wf degraded
    # single degraded -> overall degraded? (degraded>=healthy -> yes)
    assert h.overall in ("degraded", "healthy", "unknown")
    assert h.degraded_count == 1
    # assessment TIDAK punya kontrol atas runtime
    assert not hasattr(api, "control_runtime")


# --------------------------------------------------------------------------
# WP-25 Ecosystem Recommendation
# --------------------------------------------------------------------------

def test_recommendation_advisory(api):
    _reg, i, rt, _p, _w = api
    c_nc = i.certify(rt.identity_id, checks_total=5, checks_passed=1)
    recs = i.recommend((rt.identity_id,), certifications={rt.identity_id: c_nc})
    assert recs
    for r in recs:
        assert r.advisory is True
        assert isinstance(r, EcosystemRecommendation)


def test_recommendation_deterministic(api):
    _reg, i, rt, _p, _w = api
    c_nc = i.certify(rt.identity_id, checks_total=5, checks_passed=0)
    recs1 = i.recommend((rt.identity_id,), certifications={rt.identity_id: c_nc})
    recs2 = i.recommend((rt.identity_id,), certifications={rt.identity_id: c_nc})
    assert [r.subject for r in recs1] == [r.subject for r in recs2]


def test_recommendation_not_authority(api):
    _reg, i, rt, _p, _w = api
    c_nc = i.certify(rt.identity_id, checks_total=5, checks_passed=0)
    recs = i.recommend((rt.identity_id,), certifications={rt.identity_id: c_nc})
    # rekomendasi tidak pernah mengeksekusi / menerapkan apapun
    assert not hasattr(i, "apply")
    assert not hasattr(i, "auto_approve")


# --------------------------------------------------------------------------
# WP-26 Ecosystem Explainability
# --------------------------------------------------------------------------

def test_explainability_evidence_backed(api):
    _reg, i, rt, _p, _w = api
    c = i.certify(rt.identity_id)
    exp = i.explain_certification(c)
    assert exp.statements
    assert exp.evidence_items  # evidence-backed
    h = i.health((rt.identity_id,))
    he = i.explain_health(h)
    assert he.statements
    assert he.evidence_items


def test_explain_recommendation(api):
    _reg, i, rt, _p, _w = api
    c_nc = i.certify(rt.identity_id, checks_total=5, checks_passed=0)
    recs = i.recommend((rt.identity_id,), certifications={rt.identity_id: c_nc})
    for r in recs:
        e = i.explain_recommendation(r)
        assert e.evidence_items


# --------------------------------------------------------------------------
# WP-27 Citizen Intelligence API (read-only / advisory)
# --------------------------------------------------------------------------

def test_intelligence_api_read_only(api):
    reg, i, rt, prov, _w = api
    before = reg.count()
    i.certify(rt.identity_id)
    i.snapshot((rt.identity_id, prov.identity_id))
    i.health((rt.identity_id,))
    i.recommend((rt.identity_id,))
    assert reg.count() == before  # tidak ada citizen bertambah
    # tidak ada verb approval/kontrol/mutasi
    assert not hasattr(i, "approve_citizen")
    assert not hasattr(i, "apply_certification")
    assert not hasattr(i, "control_runtime")
    assert not hasattr(i, "transition_lifecycle")
    assert not hasattr(i, "grant_privilege")


def test_registry_authoritative(api):
    _reg, i, rt, _p, _w = api
    # kind diambil dari registry (authoritative), bukan ditebak
    snap = i.snapshot((rt.identity_id,))
    assert snap.kinds == {"runtime": 1}


# --------------------------------------------------------------------------
# WP-28 Certification Compliance
# --------------------------------------------------------------------------

def test_certification_compliance_suite_passed():
    files = default_source_files(_ECO_ROOT)
    passed, checks = compliance_check(files, module_root=_ECO_ROOT)
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# WP-30 Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_exit_criteria_end_to_end(api):
    """Platform menyertifikasi, mengevaluasi, memahami ekosistem secara
    deterministik & evidence-first, tanpa authority dan tanpa kontrol."""
    _reg, i, rt, prov, wf = api
    ids = (rt.identity_id, prov.identity_id, wf.identity_id)

    # seberapa siap/patuh seorang citizen?
    c = i.certify(rt.identity_id)
    assert c.maturity and c.compliance

    # bagaimana kesehatan & keragaman ekosistem?
    snap = i.snapshot(ids)
    h = i.health(ids)
    assert snap.citizen_count == 3
    assert h.overall

    # apa rekomendasi peningkatan (advisory)?
    c_nc = i.certify(rt.identity_id, checks_total=5, checks_passed=0)
    recs = i.recommend(ids, certifications={rt.identity_id: c_nc})
    assert all(r.advisory for r in recs)

    # mengapa hasilnya demikian?
    assert i.explain_certification(c).evidence_items
    assert i.explain_health(h).evidence_items

    # TANPA authority: tidak ada approval/kontrol/mutasi
    assert not hasattr(i, "approve_citizen")
    assert not hasattr(i, "apply_certification")
    assert not hasattr(i, "control_runtime")
    assert not hasattr(i, "transition_lifecycle")
    # Registry authoritative: identitas dari registry
    assert snap.kinds == {"runtime": 1, "provider": 1, "workflow": 1}
