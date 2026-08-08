"""reasoning — WP-04/05 tests (IP-3.1-001)."""

from sam.governance_intelligence.reasoning.evidence import EvidenceResolver
from sam.governance_intelligence.reasoning.engine import GovernanceReasoner, keyword_rule
from sam.governance_intelligence.reasoning.engine.reasoner import keyword_rule as _kr


def test_evidence_resolver_collect(evidence_repo):
    res = EvidenceResolver(evidence_repo)
    chain = res.collect(["Objective"])
    assert len(chain.evidence) >= 1
    assert chain.answer is not None


def test_evidence_resolver_trace(evidence_repo):
    res = EvidenceResolver(evidence_repo)
    c = res.trace("Objective")
    assert len(c) >= 1
    assert c[0].item_key  # traceable


def test_evidence_chain_public_dict(evidence_repo):
    res = EvidenceResolver(evidence_repo)
    chain = res.resolve("nothing matches this")
    assert isinstance(chain.public_dict(), dict)


def test_reasoner_rule_engine(mission_repo, evidence_repo):
    reasoner = GovernanceReasoner(mission_repo)
    rules = [("objective", keyword_rule("objective"))]
    tree = reasoner.reason("assess", rules, evidence_repo)
    assert tree.root.matched is True
    assert tree.root.confidence >= 0.0


def test_reasoner_missing_evidence(mission_repo, evidence_repo):
    reasoner = GovernanceReasoner(mission_repo)
    rules = [("none", _kr("zzz-nope-not-present"))]
    tree = reasoner.reason("gaps", rules, evidence_repo)
    # Unmatched rule -> matched False, confidence 0 (missing evidence)
    assert tree.root.matched is False
    assert tree.root.confidence == 0.0
