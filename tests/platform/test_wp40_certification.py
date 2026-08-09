# -*- coding: utf-8 -*-
"""IP-3.5-004 Explainability Experience - Certification (WP-24..28).

Menguji: Unified Evidence Graph (WP-24), Evidence Aggregation (WP-25),
Cross-domain Explainability (WP-26), Evidence Chain Viewer (WP-27),
Explainability API (WP-28), Explainability Compliance (EX).

Guardrail (IP-3.5): Explainability Experience PRESENTS evidence graph,
TIDAK memverifikasi/menolak/menilai evidence, TIDAK mengambil keputusan
/ otoritas. Seluruh evidence DIBERIKAN dari luar sebagai input.
"""

import pytest

from sam.platform import (
    DomainPairCoverage,
    EvidenceAggregate,
    EvidenceChain,
    EvidenceGraph,
    EvidenceInput,
    EvidenceLink,
    EvidenceNode,
    ExplainabilityAPI,
    ExplainabilitySnapshot,
    ExplainabilitySummary,
    aggregate_evidence,
    build_chain,
    build_evidence_graph,
    explain_graph,
    orphaned_evidence,
    explainability_compliance_check,
)


def _evid(eid, domain, status="COLLECTED", supports=()):
    return EvidenceInput(eid, domain, "type", status, "s", supports=supports)


# --- WP-24 Unified Evidence Graph -------------------------------------------

def test_evidence_requires_id():
    with pytest.raises(ValueError):
        EvidenceInput(evidence_id="")


def test_graph_build_and_normalize_status():
    g = build_evidence_graph([
        _evid("e1", "gov", status="verified"),  # lowercase -> dict as-is, status_norm upper
        _evid("e2", "runtime"),
    ])
    assert g.node_count == 2
    assert g.node("e1").status_norm == "VERIFIED"  # _norm_status meng-normalisasi
    assert g.node("e2").status_norm == "COLLECTED"


def test_graph_links_from_supports():
    g = build_evidence_graph([
        _evid("a", "gov", supports=("b",)),
        _evid("b", "runtime"),
        _evid("c", "mission", supports=("ghost",)),  # target tidak ada -> diabaikan
    ])
    assert g.link_count == 1
    assert g.links[0].source == "a"
    assert g.links[0].target == "b"


def test_graph_domain_set_sorted():
    g = build_evidence_graph([
        _evid("a", "runtime"), _evid("b", "gov"), _evid("c", "gov"),
    ])
    assert g.domain_set() == ("gov", "runtime")


# --- WP-25 Evidence Aggregation ---------------------------------------------

def test_aggregate_counts_and_verified():
    g = build_evidence_graph([
        _evid("a", "gov", status="VERIFIED"),
        _evid("b", "gov", status="VERIFIED"),
        _evid("c", "runtime", status="COLLECTED"),
    ])
    agg = aggregate_evidence(g)
    assert agg.total == 3
    assert agg.verified_count == 2
    assert agg.count_for("gov") == 2
    assert agg.count_for("runtime") == 1
    assert agg.count_for("missing") == 0


# --- WP-26 Cross-domain Explainability --------------------------------------

def test_explain_summary_cross_domain():
    g = build_evidence_graph([
        _evid("a", "gov", supports=("b",)),
        _evid("b", "runtime"),
        _evid("c", "mission"),
    ])
    s = explain_graph(g)
    # 1 link gov->runtime (cross)
    assert s.total_nodes == 3
    assert s.total_links == 1
    assert s.cross_domain_links == 1
    assert s.explainable
    assert ("gov", "runtime") in [(p.source_domain, p.target_domain)
                                  for p in s.coverage_pairs]


def test_explain_not_explainable_without_links():
    g = build_evidence_graph([_evid("a", "gov"), _evid("b", "runtime")])
    s = explain_graph(g)
    assert not s.explainable
    assert s.cross_domain_links == 0


# --- WP-27 Evidence Chain Viewer --------------------------------------------

def test_chain_direct_support():
    g = build_evidence_graph([
        _evid("a", "gov", supports=("b",)),
        _evid("b", "runtime"),
    ])
    # b didukung a -> chain b path [a, b]
    ch = build_chain(g, "b")
    assert ch is not None
    assert ch.target_id == "b"
    assert [n.evidence_id for n in ch.path] == ["a", "b"]
    assert ch.depth == 2


def test_chain_missing_target():
    g = build_evidence_graph([_evid("a", "gov")])
    assert build_chain(g, "nope") is None


def test_orphaned_evidence():
    g = build_evidence_graph([
        _evid("a", "gov", supports=("b",)),
        _evid("b", "runtime"),
        _evid("c", "mission"),  # tanpa link -> orphan
    ])
    orphans = orphaned_evidence(g)
    assert [n.evidence_id for n in orphans] == ["c"]


# --- WP-28 Explainability API -----------------------------------------------

def _setup_api():
    api = ExplainabilityAPI()
    api.register_evidence(_evid("e1", "gov", status="VERIFIED"))
    api.register_evidence(_evid("e2", "governance", status="VERIFIED", supports=("e1",)))
    api.register_evidence(_evid("e3", "runtime"))
    return api


def test_api_snapshot():
    api = _setup_api()
    snap = api.snapshot()
    assert isinstance(snap, ExplainabilitySnapshot)
    assert snap.graph.node_count == 3
    assert snap.aggregate.total == 3
    assert snap.summary.total_nodes == 3


def test_api_chain_and_orphans():
    api = _setup_api()
    ch = api.chain("e1")
    assert ch is not None  # e2 mendukung e1
    assert [n.evidence_id for n in ch.path] == ["e2", "e1"]
    assert [n.evidence_id for n in api.orphans()] == ["e3"]
    assert api.evidence_ids() == ("e1", "e2", "e3")


# --- EX compliance -----------------------------------------------------------

def test_explain_compliance_passes():
    res = explainability_compliance_check()
    assert res.ok, res.messages
    assert res.group == "EX"
    assert res.forbidden_found == ()


# --- Exit criteria: presentation-passive evidence ---------------------------

def test_explain_api_has_no_judgment_verbs():
    names = [n for n in dir(ExplainabilityAPI) if not n.startswith("_")]
    forbidden = {"verify_evidence", "reject_evidence", "decide", "judge",
                 "infer_authority", "grant_authority", "approve_evidence"}
    assert not (forbidden & set(names))
