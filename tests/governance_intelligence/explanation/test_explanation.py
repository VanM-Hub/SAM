"""explanation — WP-06 tests (IP-3.1-001)."""

from sam.governance_intelligence.explanation.decision import build_explanation, explanation_summary
from sam.governance_intelligence.reasoning.engine import GovernanceReasoner, keyword_rule


def test_build_explanation_contains_evidence(mission_repo, evidence_repo):
    reasoner = GovernanceReasoner(mission_repo)
    tree = reasoner.reason("assess", [("objective", keyword_rule("objective"))], evidence_repo)
    expl = build_explanation(tree)
    assert expl.evidence  # evidence present
    assert isinstance(expl.rationale, str)
    assert expl.confidence == tree.root.confidence


def test_explanation_missing_evidence(mission_repo, evidence_repo):
    reasoner = GovernanceReasoner(mission_repo)
    tree = reasoner.reason("gaps", [("nope", keyword_rule("zzz-absent"))], evidence_repo)
    expl = build_explanation(tree)
    assert expl.missing_evidence  # flagged missing
    assert expl.confidence == 0.0


def test_explanation_public_dict_and_summary(mission_repo, evidence_repo):
    reasoner = GovernanceReasoner(mission_repo)
    tree = reasoner.reason("a", [("objective", keyword_rule("objective"))], evidence_repo)
    expl = build_explanation(tree)
    assert isinstance(expl.public_dict(), dict)
    assert isinstance(explanation_summary(expl), str)
