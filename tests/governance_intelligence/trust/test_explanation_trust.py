"""WP-19..20 - Explanation Composer + Trust Score tests (IP-3.1-002).

Verifies:
  - WP-19: explanations always have the fixed structure (Summary, Evidence,
    Governance Basis, Architectural Basis, Confidence, Missing Information);
    no free-form narration.
  - WP-20: trust is computed from evidence quality dimensions, not a
    confidence model.
"""

from __future__ import annotations

import pytest

from sam.governance_intelligence.explanation.composer import ExplanationComposer, StructuredExplanation
from sam.governance_intelligence.trust import TrustAssessment, TrustScoreEngine
from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.indexes import index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import EvidenceRepository, MissionRepository
from sam.governance_intelligence.reasoning.engine.reasoner import GovernanceReasoner, keyword_rule


def _tree():
    text = "# Mission\n\nGovern with evidence.\n"
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", text))
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", text))
    reasoner = GovernanceReasoner(mission)
    return reasoner.reason("govern", [("govern", keyword_rule("govern"))], evidence), evidence


class TestExplanationComposer:
    FIXED_KEYS = {
        "summary", "evidence", "governance_basis",
        "architectural_basis", "confidence", "missing_information",
    }

    def test_structured_explanation_has_all_fields(self):
        tree, evidence = _tree()
        expl = ExplanationComposer().compose(tree)
        assert isinstance(expl, StructuredExplanation)
        assert set(expl.public_dict()) == self.FIXED_KEYS

    def test_no_free_form_narration(self):
        tree, evidence = _tree()
        expl = ExplanationComposer().compose(tree)
        d = expl.public_dict()
        # structure is fixed: summary is a single sentence referencing goal,
        # all other fields are lists or a float
        assert isinstance(d["summary"], str)
        assert isinstance(d["evidence"], list)
        assert isinstance(d["governance_basis"], list)
        assert isinstance(d["architectural_basis"], list)
        assert isinstance(d["confidence"], float)
        assert isinstance(d["missing_information"], list)

    def test_confidence_in_range(self):
        tree, evidence = _tree()
        expl = ExplanationComposer().compose(tree)
        assert 0.0 <= expl.confidence <= 1.0


class TestTrustScore:
    def _repo(self, items):
        return EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", "x"))

    def test_assess_empty(self):
        repo = self._repo([])
        t: TrustAssessment = TrustScoreEngine(repo).assess([])
        assert isinstance(t, TrustAssessment)
        assert t.overall == 0.0

    def test_assess_populated(self):
        text = "# Mission\n\nGovern with evidence.\n"
        repo = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", text))
        t = TrustScoreEngine(repo).assess(repo.all())
        assert 0.0 <= t.overall <= 1.0
        for dim in ("completeness", "source_authority", "consistency",
                    "freshness", "verification_status", "constitutional_compliance"):
            assert 0.0 <= getattr(t, dim) <= 1.0, dim

    def test_public_dict_keys(self):
        text = "# Mission\n\nGovern with evidence.\n"
        repo = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", text))
        d = TrustScoreEngine(repo).assess(repo.all()).public_dict()
        assert "overall" in d and "completeness" in d and "source_authority" in d
