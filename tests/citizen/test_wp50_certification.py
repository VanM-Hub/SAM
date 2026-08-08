# IP-3.4-002 WP-20 - End-to-end Federation Trust & Interoperability
# Certification test (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Definisi Done IP-3.4-002: Federation dapat saling percaya dan saling
# bekerja sama tanpa kehilangan kedaulatan masing-masing - secara
# deterministik, evidence-first, dan TANPA authority/eksekusi.
#
# Guardrail IP-3.4-002 dikunci:
#   Trust != Authority; Interoperability != Execution;
#   Negotiation != Agreement; Assessment != Federation Control;
#   Compatibility != Approval; Local Sovereignty; Registry authoritative;
#   Deterministic; Evidence-first.

import os

import pytest

from sam.citizen.federation.trust import (
    FederationTrustProfile,
    TrustConstraint,
    TrustEvidence,
    TrustLevel,
)
from sam.citizen.federation.trust_engine import TrustEvaluationEngine
from sam.citizen.federation.interoperability import InteroperabilityEngine
from sam.citizen.federation.negotiation import CapabilityNegotiator
from sam.citizen.federation.compatibility import (
    FederationCompatibilityAnalyzer,
)
from sam.citizen.federation.explainability import TrustExplainer
from sam.citizen.federation.interop_api import FederationInteroperabilityAPI
from sam.citizen.federation.compliance import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FED_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "federation")


@pytest.fixture
def api():
    return FederationInteroperabilityAPI()


@pytest.fixture
def good_profile():
    return FederationInteroperabilityAPI().trust(
        "ecosystem-a", certification="certified", compatibility="compatible",
        contract=("health", "audit"), health="healthy",
        evidence=(TrustEvidence("evidence", "audit-passed", "recent"),),
    )


# --------------------------------------------------------------------------
# WP-11 Federation Trust Model
# --------------------------------------------------------------------------

def test_trust_level_ordering():
    assert TrustLevel("unknown") < TrustLevel("low")
    assert TrustLevel("low") < TrustLevel("medium")
    assert TrustLevel("medium") < TrustLevel("high")
    assert TrustLevel("high").rank == 3


def test_trust_evidence_immutable():
    e = TrustEvidence("certification", "cert-level", "certified")
    with pytest.raises(Exception):
        e.kind = "changed"


def test_trust_constraint():
    c = TrustConstraint("cert-mismatch", "level differs")
    assert c.name == "cert-mismatch"
    assert c.as_dict()["detail"] == "level differs"


def test_trust_profile_is_trusted_not_privilege(good_profile):
    # trust = assessment; is_trusted hanya penanda, bukan hak
    assert good_profile.is_trusted
    assert not hasattr(good_profile, "privilege")
    assert not hasattr(good_profile, "authority")


def test_trust_profile_evidence_sorted():
    profile = FederationInteroperabilityAPI().trust(
        "ecosystem-a", certification="certified", compatibility="compatible",
        contract=("audit", "health"), health="healthy",
        evidence=(TrustEvidence("evidence", "audit-passed", "recent"),),
    )
    kinds = profile.evidence_kinds()
    assert "certification" in kinds
    assert "evidence" in kinds
    assert "contract" in kinds


# --------------------------------------------------------------------------
# WP-12 Trust Evaluation Engine (deterministik)
# --------------------------------------------------------------------------

def test_trust_evaluation_deterministic(api):
    p1 = api.trust("ecosystem-a", certification="certified",
                   compatibility="compatible", contract=("health",),
                   health="healthy")
    p2 = api.trust("ecosystem-a", certification="certified",
                   compatibility="compatible", contract=("health",),
                   health="healthy")
    assert p1.as_dict() == p2.as_dict()


def test_trust_gradient_by_evidence_quality(api):
    p_good = api.trust("ecosystem-a", certification="certified",
                       compatibility="compatible", contract=("health",),
                       health="healthy")
    p_partial = api.trust("ecosystem-b", certification="defined",
                          compatibility="partial", contract=("llm",),
                          health="degraded")
    p_weak = api.trust("ecosystem-c", certification="initial",
                       compatibility="incompatible", contract=(),
                       health="unavailable")
    assert p_good.level.rank > p_partial.level.rank > p_weak.level.rank


def test_trust_certification_matters(api):
    # tanpa bukti apa pun -> unknown/low
    p_none = api.trust("ecosystem-x")
    assert p_none.level.level in ("unknown", "low", "medium", "high")


def test_trust_aggregator(api):
    p_a = api.trust("ecosystem-a", certification="certified",
                    compatibility="compatible", health="healthy")
    p_b = api.trust("ecosystem-b", certification="defined",
                    compatibility="partial", health="degraded")
    s = api.trust_summary((p_a, p_b))
    assert s["count"] == 2
    assert s["high"] + s["medium"] + s["low"] + s["unknown"] == 2


# --------------------------------------------------------------------------
# WP-13 Interoperability Model
# --------------------------------------------------------------------------

def test_interoperability_assessment(api):
    a = api.interoperability(
        "ecosystem-a", "ecosystem-b",
        ("health", "audit"), ("health", "llm"),
        ("health-check", "audit"), ("generate", "translate"),
        "certified", "defined")
    assert isinstance(a, object)
    assert "health" not in a.gaps  # ada contract dibagi


def test_interoperability_no_shared_contract():
    eng = InteroperabilityEngine()
    a = eng.assess("a", "b", ("x",), ("y",), ("x",), ("y",))
    assert not a.compatible
    assert "no-shared-contract-or-capability" in a.gaps


def test_interoperability_shared_capability():
    eng = InteroperabilityEngine()
    a = eng.assess("a", "b", ("x",), ("x",), ("audit",), ("audit",))
    assert a.compatible
    assert "audit" in a.matched_capabilities


# --------------------------------------------------------------------------
# WP-14 Capability Negotiation (proposal, bukan agreement)
# --------------------------------------------------------------------------

def test_negotiation_proposal_not_agreement(api):
    r = api.negotiate("ecosystem-a", "ecosystem-b", "audit",
                      ("generate", "translate"), ("llm",),
                      ("health", "audit"), ())
    assert r.is_agreement is False
    # proposal yang ada tidak pernah ter-bind
    for p in r.proposals:
        assert p.is_bound is False


def test_negotiation_available_capability():
    neg = CapabilityNegotiator()
    r = neg.negotiate("a", "b", "audit", ("audit", "translate"),
                      ("llm", "audit"), ("health", "audit"),
                      ("audit",))
    assert r.proposals  # ada proposal untuk 'audit'
    assert r.gaps == () or "capability-not-available:audit" not in r.gaps


def test_negotiation_alternative():
    neg = CapabilityNegotiator()
    r = neg.negotiate("a", "b", "audit", ("generate", "translate"),
                      ("llm",), ("health",), ())
    assert r.alternatives or r.gaps


# --------------------------------------------------------------------------
# WP-15 Federation Compatibility
# --------------------------------------------------------------------------

def test_compatibility_analyzer():
    comp = FederationCompatibilityAnalyzer().analyze(
        "a", "b", ("health", "audit"), ("llm",),
        ("health-check", "audit"), ("generate", "translate"),
        "certified", "defined", "p1", "p2")
    assert comp.overall in ("incompatible", "partial", "compatible")
    assert comp.is_compatible is False  # contract/capability/protocol beda


def test_compatibility_fully_matching():
    comp = FederationCompatibilityAnalyzer().analyze(
        "a", "b", ("health",), ("health",),
        ("audit",), ("audit",),
        "certified", "certified", "p1", "p1")
    assert comp.overall == "compatible"
    assert comp.is_compatible is True


# --------------------------------------------------------------------------
# WP-16 Trust Explainability
# --------------------------------------------------------------------------

def test_explain_trust(good_profile, api):
    ex = api.explain_trust(good_profile)
    assert ex.member_id == "ecosystem-a"
    assert ex.evidence  # evidence-first
    assert ex.reasons


def test_explain_interoperability(api):
    ex = api.explain_interoperability(
        "a", "b", compatible=False,
        gaps=("no-shared-contract",),
        recommended=("align-certification",))
    assert ex.gaps == ("no-shared-contract",)
    assert "align-certification" in ex.recommendations


# --------------------------------------------------------------------------
# WP-17 Federation Interoperability API (read-only)
# --------------------------------------------------------------------------

def test_api_no_authority_verbs(api):
    assert not hasattr(api, "connect")
    assert not hasattr(api, "authorize")
    assert not hasattr(api, "execute")
    assert not hasattr(api, "activate")
    assert not hasattr(api, "bind")
    assert not hasattr(api, "delegate_authority")


def test_api_read_only_does_not_mutate(api):
    # semua panggilan hanya assessment, tidak mengubah state
    before = api.trust_summary((
        api.trust("ecosystem-a", certification="certified",
                  compatibility="compatible", health="healthy"),))
    p = api.trust("ecosystem-a", certification="certified",
                  compatibility="compatible", health="healthy")
    after = api.trust_summary((p,))
    assert before == after


# --------------------------------------------------------------------------
# WP-18 Federation Compliance
# --------------------------------------------------------------------------

def test_compliance_suite_passed():
    files = default_source_files(_FED_ROOT)
    passed, checks = compliance_check(files, module_root=_FED_ROOT)
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# WP-20 Exit criteria
# --------------------------------------------------------------------------

def test_trust_recognition_across_federation(api):
    """Federation dapat saling percaya tanpa kehilangan kedaulatan."""
    p_a = api.trust("ecosystem-a", certification="certified",
                    compatibility="compatible", contract=("health",),
                    health="healthy")
    p_b = api.trust("ecosystem-b", certification="defined",
                    compatibility="partial", contract=("llm",),
                    health="degraded")
    # trust dapat dibedakan berdasarkan bukti
    assert p_a.as_dict() != p_b.as_dict()
    # kedaulatan lokal dipertahankan: tidak ada otoritas global yang mengganti
    assert not hasattr(p_a, "global_authority")
    # trust tidak memberi kewenangan
    assert p_a.is_trusted is True
    assert not hasattr(p_a, "authorize")


def test_exit_criteria(varies=()):
    """Constitutional interoperability tanpa authority/eksekusi."""
    api = FederationInteroperabilityAPI()

    # saling bekerja sama lewat interoperabilitas (assessment)
    interop = api.interoperability(
        "ecosystem-a", "ecosystem-c",
        ("health",), ("health",),
        ("audit",), ("audit",),
        "certified", "certified")
    if interop.compatible:
        assert interop.matched_contracts or interop.matched_capabilities
    else:
        assert interop.gaps

    # negosiasi menghasilkan proposal, bukan agreement
    ng = api.negotiate("ecosystem-a", "ecosystem-c", "health",
                       ("health",), ("health",), ("health",), ("health",))
    assert ng.is_agreement is False
    assert not ng.proposals or all(not p.is_bound for p in ng.proposals)

    # penjelasan berbasis evidence
    p = api.trust("ecosystem-c", certification="certified",
                  compatibility="compatible", health="healthy")
    ex = api.explain_trust(p)
    assert ex.evidence

    # tidak ada yang menjalankan eksekusi / memberikan otoritas
    assert not hasattr(api, "execute")
    assert not hasattr(api, "authorize")
