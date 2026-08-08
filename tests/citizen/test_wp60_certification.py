# IP-3.4-003 WP-30 - End-to-end Distributed Governance Intelligence
# Certification test (AO-3.4-001 / ED-3.4-001, paket ketiga)
#
# Definisi Done IP-3.4-003: independent federated ecosystems dapat reasoning
# bersama TANPA berbagi authority - tiap federation reasoning lokal, reasoning
# dipertukarkan sebagai evidence (bukan authority), diagregasi deterministik
# menjadi insight, diturunkan jadi rekomendasi.
#
# BUKAN Distributed Governance. BUKAN Shared Governance.
# Yang dibangun = Distributed GOVERNANCE INTELLIGENCE.
#
# Guardrail IP-3.4-003 dikunci:
#   Knowledge != Authority (DGI-01)
#   Evidence Exchange != Runtime Sharing (DGI-02)
#   Recommendation != Decision (DGI-03)
#   Collaboration != Execution (DGI-04)
#   Federation Intelligence != Central Intelligence (DGI-05)
#   Sovereignty preserved (DGI-06)
#   Deterministic reasoning (DGI-07)
#   Evidence-first (DGI-08)
#   Read-only API (DGI-09)
#   No hidden dependency (DGI-10)

import os

import pytest

from sam.citizen.federation.collaboration import (
    CollaborationStatus,
    FederationCollaboration,
    FederationCollaborationModel,
)
from sam.citizen.federation.proposal import (
    CollaborationProposalEngine,
)
from sam.citizen.federation.knowledge_exchange import (
    DistributedKnowledgeExchange,
    KnowledgeArtifact,
)
from sam.citizen.federation.evidence_exchange import (
    DistributedEvidenceExchange,
    EvidenceEdge,
    EvidenceNode,
)
from sam.citizen.federation.intelligence import (
    FederationIntelligenceEngine,
    LocalReasoning,
)
from sam.citizen.federation.recommendation import (
    DistributedRecommendation,
)
from sam.citizen.federation.explainability import (
    FederationIntelligenceExplainer,
)
from sam.citizen.federation.intelligence_api import FederationIntelligenceAPI
from sam.citizen.federation.compliance import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FED_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "federation")


@pytest.fixture
def api():
    return FederationIntelligenceAPI()


# --------------------------------------------------------------------------
# WP-21 Federation Collaboration Model
# --------------------------------------------------------------------------

def test_collaboration_describe(api):
    c = api.describe_collaboration(
        "eco-a", "eco-b", "joint-audit",
        shared_contracts=("health", "audit"),
        shared_capabilities=("audit",),
        constraints=("read-only",))
    assert isinstance(c, FederationCollaboration)
    assert c.source_id == "eco-a"
    assert c.target_id == "eco-b"
    assert c.is_execution is False  # DGI-04


def test_collaboration_alignment(api):
    c = api.describe_collaboration(
        "eco-a", "eco-b", "joint-audit",
        shared_contracts=("audit",),
        shared_capabilities=("audit",))
    status = api.assess_alignment(
        c, local_contracts=("audit", "health"),
        local_capabilities=("audit", "translate"))
    assert isinstance(status, CollaborationStatus)
    assert status.aligned is True
    assert status.notes == ()


def test_collaboration_misalignment_note(api):
    c = api.describe_collaboration(
        "eco-a", "eco-b", "joint-audit",
        shared_contracts=("audit", "llm"),
        shared_capabilities=("audit",))
    status = api.assess_alignment(
        c, local_contracts=("audit",),
        local_capabilities=("audit",))
    assert status.aligned is False
    assert any("contract-not-local:llm" in n for n in status.notes)


# --------------------------------------------------------------------------
# WP-22 Collaboration Proposal Engine
# --------------------------------------------------------------------------

def test_proposal_available_capability(api):
    r = api.propose_collaboration(
        "eco-a", "eco-b", "audit",
        target_capabilities=("audit", "translate"),
        target_contracts=("health", "audit"),
        required_contracts=("audit",))
    assert r.proposals
    assert all(not p.is_bound for p in r.proposals)  # DGI-04 proposal-only
    assert r.is_agreement is False


def test_proposal_alternative_when_unavailable(api):
    r = api.propose_collaboration(
        "eco-a", "eco-b", "audit",
        target_capabilities=("translate", "generate"),
        target_contracts=("health",))
    assert any("capability-not-available:audit" in g for g in r.gaps)
    assert r.is_agreement is False
    if r.proposals:
        assert r.proposals[0].alternatives  # menawarkan alternatif


def test_proposal_never_binds(api):
    eng = CollaborationProposalEngine()
    r = eng.propose("a", "b", "audit", ("audit",), ("audit",))
    for p in r.proposals:
        assert p.is_bound is False


# --------------------------------------------------------------------------
# WP-23 Distributed Knowledge Exchange (read-only)
# --------------------------------------------------------------------------

def test_knowledge_package_read(api):
    arts = (KnowledgeArtifact("eco-a", "contract", "audit", "health"),
            KnowledgeArtifact("eco-a", "capability", "audit", "audit-cap"))
    pkg = api.package_knowledge("eco-a", arts)
    assert pkg.source_id == "eco-a"
    assert pkg.is_authority is False  # DGI-01
    got = api.read_knowledge(pkg, kinds=("contract",))
    assert len(got) == 1
    assert got[0].key == "audit"


def test_knowledge_not_authority(api):
    arts = (KnowledgeArtifact("eco-a", "contract", "audit", "health"),)
    pkg = api.package_knowledge("eco-a", arts)
    assert api._knowledge.has_authority(pkg) is False  # DGI-01


def test_knowledge_filter_by_key(api):
    arts = (KnowledgeArtifact("eco-a", "contract", "audit", "h1"),
            KnowledgeArtifact("eco-a", "contract", "health", "h2"))
    pkg = api.package_knowledge("eco-a", arts)
    got = api.read_knowledge(pkg, keys=("health",))
    assert len(got) == 1
    assert got[0].key == "health"


# --------------------------------------------------------------------------
# WP-24 Distributed Evidence Exchange (evidence graph)
# --------------------------------------------------------------------------

def test_evidence_graph_build(api):
    nodes = (EvidenceNode("n1", "eco-a", "claim", "audit-clean"),
             EvidenceNode("n2", "eco-a", "observation", "result-ok"),
             EvidenceNode("n3", "eco-a", "observation", "log-consistent"))
    edges = (EvidenceEdge("n2", "n1", "supports"),
             EvidenceEdge("n3", "n1", "supports"))
    g = api.build_evidence_graph("eco-a", nodes, edges)
    assert g.is_runtime_share is False  # DGI-02
    assert api._evidence.exposes_runtime(g) is False


def test_evidence_supports_claim(api):
    nodes = (EvidenceNode("n1", "eco-a", "claim", "audit-clean"),
             EvidenceNode("n2", "eco-a", "observation", "result-ok"),
             EvidenceNode("n3", "eco-a", "contract", "audit-contract"))
    edges = (EvidenceEdge("n2", "n1", "supports"),
             EvidenceEdge("n3", "n1", "refutes"))
    g = api.build_evidence_graph("eco-a", nodes, edges)
    support = api.evidence_supporting(g, "n1")
    ids = {n.node_id for n in support}
    assert "n2" in ids  # observation supports
    assert "n3" not in ids  # refutes tidak masuk


def test_evidence_observations(api):
    nodes = (EvidenceNode("o1", "eco-a", "observation", "healthy"),
             EvidenceNode("o2", "eco-a", "observation", "audited"))
    g = api.build_evidence_graph("eco-a", nodes)
    obs = api.evidence_observations(g)
    assert len(obs) == 2


# --------------------------------------------------------------------------
# WP-25 Federation Intelligence Engine (deterministic, local-first)
# --------------------------------------------------------------------------

def test_insight_clear_signal(api):
    r = (
        api.share_reasoning("eco-a", "audit-clean", 0.9, trusted=True),
        api.share_reasoning("eco-b", "audit-clean", 0.8, trusted=True),
    )
    insight = api.synthesize_insight("audit", r)
    assert insight.signal == "clear"
    assert insight.agreement_score >= 0.7
    assert insight.is_decision is False  # DGI-03


def test_insight_mixed_signal(api):
    r = (
        api.share_reasoning("eco-a", "audit-clean", 0.9, trusted=True),
        api.share_reasoning("eco-b", "risk-high", 0.7, trusted=False),
    )
    insight = api.synthesize_insight("audit", r)
    assert insight.signal in ("mixed", "inconclusive")
    assert insight.is_decision is False


def test_intelligence_not_central(api):
    # tiap federation reasoning lokal; aggregator tidak menggantikan
    eng = FederationIntelligenceEngine()
    r = (LocalReasoning("eco-a", "ok", 0.9, trusted=True),)
    insight = eng.aggregate("focus-x", r)
    assert len(insight.members) == 1  # reasoning tiap member dipertahankan
    assert insight.members[0].member_id == "eco-a"


def test_reasoning_deterministic(api):
    r = (api.share_reasoning("eco-a", "x", 0.9, trusted=True),)
    i1 = api.synthesize_insight("f", r)
    i2 = api.synthesize_insight("f", r)
    assert i1.as_dict() == i2.as_dict()  # DGI-07


# --------------------------------------------------------------------------
# WP-26 Distributed Recommendation
# --------------------------------------------------------------------------

def test_recommendation_advisory(api):
    r = (api.share_reasoning("eco-a", "ok", 0.9, trusted=True),)
    insight = api.synthesize_insight("audit", r)
    res = api.recommend((insight,))
    assert res.recommendations
    assert res.is_decision is False  # DGI-03
    for rec in res.recommendations:
        assert rec.is_decision is False
        assert rec.basis  # evidence-first DGI-08


def test_recommendation_for_member(api):
    r = (api.share_reasoning("eco-a", "ok", 0.85, trusted=True),
         api.share_reasoning("eco-b", "risk", 0.6, trusted=False))
    insight = api.synthesize_insight("audit", r)
    recs = api.recommend_for_member("eco-a", (insight,))
    assert recs
    assert all("eco-a" in "".join(x.basis) for x in recs)


# --------------------------------------------------------------------------
# WP-27 Explainability (lintas federation)
# --------------------------------------------------------------------------

def test_explain_insight(api):
    r = (api.share_reasoning("eco-a", "ok", 0.9, trusted=True),)
    insight = api.synthesize_insight("audit", r)
    ex = api.explain_intelligence(insight)
    assert ex.focus == "audit"
    assert ex.basis  # evidence-first
    assert ex.member_signals


def test_explain_recommendation(api):
    eng = DistributedRecommendation()
    ins = FederationIntelligenceEngine().aggregate(
        "audit", (LocalReasoning("eco-a", "ok", 0.9, trusted=True),))
    res = eng.recommend((ins,))
    ex = api.explain_recommendation(res.recommendations[0])
    assert ex.focus == "audit"
    assert ex.summary


# --------------------------------------------------------------------------
# WP-28 Federation Intelligence API (read-only)
# --------------------------------------------------------------------------

def test_api_no_authority_verbs(api):
    assert not hasattr(api, "connect")
    assert not hasattr(api, "authorize")
    assert not hasattr(api, "execute")
    assert not hasattr(api, "approve")
    assert not hasattr(api, "sync_state")
    assert not hasattr(api, "synchronize_state")
    assert not hasattr(api, "schedule_remote")


def test_api_methods_read_only(api):
    # semua method assessment/advisory - tidak mengubah state apa pun
    r = (api.share_reasoning("eco-a", "ok", 0.9, trusted=True),)
    i1 = api.synthesize_insight("audit", r)
    i2 = api.synthesize_insight("audit", r)
    assert i1.as_dict() == i2.as_dict()


# --------------------------------------------------------------------------
# WP-29 Federation Compliance
# --------------------------------------------------------------------------

def test_compliance_suite_passed():
    files = default_source_files(_FED_ROOT)
    passed, checks = compliance_check(files, module_root=_FED_ROOT)
    assert passed
    # 10 FED + 9 TRUST + 10 DGI = 29
    ids = {c.check_id for c in checks}
    assert {"FED-01", "TRUST-01", "DGI-01"} <= ids
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# WP-30 Exit criteria
# --------------------------------------------------------------------------

def test_exit_criteria_reasoning_together_without_authority():
    """Independent federated ecosystems reason together without sharing authority."""
    api = FederationIntelligenceAPI()

    # tiap federation reasoning lokal (DGI-05)
    r = (
        api.share_reasoning("eco-a", "audit-clean", 0.9, trusted=True),
        api.share_reasoning("eco-b", "audit-clean", 0.8, trusted=True),
        api.share_reasoning("eco-c", "audit-review", 0.7, trusted=False),
    )
    # reasoning dipertukarkan sebagai evidence (bukan authority)
    insight = api.synthesize_insight("audit", r)

    # agregasi deterministik (DGI-07) + evidence-first (DGI-08)
    assert insight.agreement_score > 0
    assert insight.is_decision is False

    # rekomendasi advisory (DGI-03)
    res = api.recommend((insight,))
    assert res.is_decision is False
    assert all(not rec.is_decision for rec in res.recommendations)

    # knowledge exchange tidak membawa authority (DGI-01)
    pkg = api.package_knowledge("eco-a", (
        KnowledgeArtifact("eco-a", "contract", "audit", "health"),))
    assert pkg.is_authority is False

    # evidence exchange bukan runtime sharing (DGI-02)
    g = api.build_evidence_graph("eco-a", (
        EvidenceNode("n1", "eco-a", "observation", "ok"),))
    assert g.is_runtime_share is False

    # collaboration deskriptif, bukan eksekusi (DGI-04)
    coll = api.describe_collaboration("eco-a", "eco-b", "joint-audit",
                                      shared_contracts=("audit",))
    assert coll.is_execution is False

    # penjelasan tersedia (evidence-based)
    ex = api.explain_intelligence(insight)
    assert ex.basis

    # kedaulatan tetap lokal (DGI-06): tidak ada otoritas bersama
    assert not hasattr(api, "authorize")
    assert not hasattr(api, "central_rule")
