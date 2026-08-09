"""Test IP-4.3-002 - Operational Knowledge (MISSION-4.3).

Coverage: WP-11..WP-20 - case repository, retrieval, similarity, lesson
extraction, knowledge, index, API, explainability, compliance, e2e.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_learning.persistent_storage import (
    PersistenceEngine,
    StorageConfig,
)
from sam.operational_learning.case_repository import Case, CaseRepository
from sam.operational_learning.case_retrieval import CaseRetriever
from sam.operational_learning.similarity_engine import SimilarityEngine
from sam.operational_learning.lesson_extraction import LessonExtractor
from sam.operational_learning.operational_knowledge import (
    KnowledgeIndex,
    OperationalKnowledge,
)
from sam.operational_learning.knowledge_api import KnowledgeAPI
from sam.operational_learning.knowledge_explainability import KnowledgeExplainer
from sam.operational_learning.knowledge_compliance import (
    KnowledgeComplianceChecker,
)


def _case_engine(tmp_path):
    return PersistenceEngine(StorageConfig(base_dir=str(tmp_path), collection="case"))


def _case(title="restart provider", outcome="success", features=()):
    return Case(
        case_id=None,
        title=title,
        description=title,
        outcome=outcome,
        features=tuple(features or ()),
        evidence_ids=("e1", "e2"),
    )


def _case_repo(tmp_path):
    repo = CaseRepository(_case_engine(tmp_path))
    c = _case()
    import uuid
    c = Case(
        case_id=uuid.uuid4().hex,
        title=c.title,
        outcome=c.outcome,
        features=c.features,
        evidence_ids=c.evidence_ids,
    )
    repo.add(c)
    return repo, c


# ---------------------------------------------------------------------------
# WP-11 Case Repository
# ---------------------------------------------------------------------------

class TestCaseRepository:
    def test_add_and_get(self, tmp_path):
        repo, c = _case_repo(tmp_path)
        assert repo.get(c.case_id) is not None
        assert repo.count() == 1

    def test_append_only_rejects_duplicate(self, tmp_path):
        repo, c = _case_repo(tmp_path)
        with pytest.raises(ValueError):
            repo.add(c)

    def test_search(self, tmp_path):
        repo = CaseRepository(_case_engine(tmp_path))
        import uuid
        repo.add(Case(case_id=uuid.uuid4().hex, title="cpu high", outcome="failed"))
        repo.add(Case(case_id=uuid.uuid4().hex, title="memory leak", outcome="success"))
        assert len(repo.search("cpu")) == 1

    def test_persistent(self, tmp_path):
        path = str(tmp_path)
        e1 = PersistenceEngine(StorageConfig(base_dir=path, collection="case"))
        repo1 = CaseRepository(e1)
        import uuid
        c = Case(case_id=uuid.uuid4().hex, title="persist me", outcome="success")
        repo1.add(c)
        e2 = PersistenceEngine(StorageConfig(base_dir=path, collection="case"))
        repo2 = CaseRepository(e2)
        assert repo2.get(c.case_id) is not None


# ---------------------------------------------------------------------------
# WP-13 Similarity Engine
# ---------------------------------------------------------------------------

class TestSimilarityEngine:
    def test_exact_match_high_score(self):
        a = _case(features=(("kind", "restart"), ("env", "prod")))
        b = _case(features=(("kind", "restart"), ("env", "prod")))
        s = SimilarityEngine().similarity(a, b)
        assert s.score == 1.0

    def test_partial_match(self):
        a = _case(features=(("kind", "restart"), ("env", "prod")))
        b = _case(features=(("kind", "restart"), ("env", "dev")))
        s = SimilarityEngine().similarity(a, b)
        assert 0 < s.score < 1.0

    def test_no_features_zero(self):
        a = _case(features=())
        b = _case(features=())
        s = SimilarityEngine().similarity(a, b)
        assert s.score == 0.0


# ---------------------------------------------------------------------------
# WP-12 Case Retrieval
# ---------------------------------------------------------------------------

class TestCaseRetrieval:
    def test_retrieve_relevant(self, tmp_path):
        repo = CaseRepository(_case_engine(tmp_path))
        import uuid
        repo.add(Case(case_id=uuid.uuid4().hex, title="cpu", features=(("kind", "restart"),)))
        repo.add(Case(case_id=uuid.uuid4().hex, title="memory", features=(("kind", "grow"),)))
        retriever = CaseRetriever(repo)
        query = _case(features=(("kind", "restart"),))
        results = retriever.retrieve(query, limit=5)
        assert len(results) >= 1
        assert results[0].score.score >= 0.5


# ---------------------------------------------------------------------------
# WP-14 Lesson Extraction
# ---------------------------------------------------------------------------

class TestLessonExtraction:
    def test_extract_success_optimization(self):
        case = _case(outcome="success")
        lesson = LessonExtractor.extract(case)
        assert lesson.category == "optimization"
        assert lesson.source_case_id == case.case_id

    def test_extract_failure_prevention(self):
        case = _case(outcome="failed")
        lesson = LessonExtractor.extract(case)
        assert lesson.category == "prevention"

    def test_lesson_has_evidence(self):
        case = _case(outcome="success")
        lesson = LessonExtractor.extract(case)
        assert lesson.source_evidence == ("e1", "e2")


# ---------------------------------------------------------------------------
# WP-15/16 Operational Knowledge + Index
# ---------------------------------------------------------------------------

class TestOperationalKnowledge:
    def test_build_knowledge_from_case(self, tmp_path):
        repo, c = _case_repo(tmp_path)
        lesson = LessonExtractor.extract(c)
        knowledge = OperationalKnowledge()
        entry = knowledge.build_from_case(c, lesson)
        assert knowledge.index.count() == 1
        assert entry.evidence_ids == ("e1", "e2")
        assert entry.confidence > 0

    def test_knowledge_index_search(self):
        index = KnowledgeIndex()
        from sam.operational_learning.operational_knowledge import KnowledgeEntry
        index.add(KnowledgeEntry(knowledge_id="k1", title="CPU spike", content="restart"))
        assert len(index.search("cpu")) == 1
        assert len(index.search()) == 1


# ---------------------------------------------------------------------------
# WP-17 Knowledge API
# ---------------------------------------------------------------------------

class TestKnowledgeAPI:
    def test_query_knowledge(self, tmp_path):
        repo, c = _case_repo(tmp_path)
        lesson = LessonExtractor.extract(c)
        knowledge = OperationalKnowledge()
        entry = knowledge.build_from_case(c, lesson)
        api = KnowledgeAPI(knowledge=knowledge.index, cases=repo)
        result = api.knowledge.search("cpu" if "cpu" in c.title else c.title[:5])
        assert api.knowledge_count() == 1
        assert api.case_count() == 1


# ---------------------------------------------------------------------------
# WP-18 Knowledge Explainability
# ---------------------------------------------------------------------------

class TestKnowledgeExplainability:
    def test_explain_knowledge_trace(self, tmp_path):
        repo, c = _case_repo(tmp_path)
        lesson = LessonExtractor.extract(c)
        knowledge = OperationalKnowledge()
        entry = knowledge.build_from_case(c, lesson)
        explainer = KnowledgeExplainer()
        expl = explainer.explain(entry, (c,))
        assert expl.trace.source_case_ids == (c.case_id,)
        assert expl.trace.evidence_ids == ("e1", "e2")
        assert "case" in expl.trace.lesson_content.lower()


# ---------------------------------------------------------------------------
# WP-19 Knowledge Compliance
# ---------------------------------------------------------------------------

class TestKnowledgeCompliance:
    def test_certify_clean(self):
        checker = KnowledgeComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_execution(self):
        checker = KnowledgeComplianceChecker()
        assert not checker.certify(execution=True)["certified"]

    def test_detects_missing_evidence(self):
        checker = KnowledgeComplianceChecker()
        assert not checker.check(all_have_evidence=False).passed


# ---------------------------------------------------------------------------
# WP-20 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestOperationalKnowledgeEndToEnd:
    def test_end_to_end_knowledge(self, tmp_path):
        path = str(tmp_path)
        e1 = PersistenceEngine(StorageConfig(base_dir=path, collection="case"))
        repo = CaseRepository(e1)
        import uuid
        c1 = Case(case_id=uuid.uuid4().hex, title="provider down", outcome="failed",
                  features=(("kind", "restart"), ("env", "prod")), evidence_ids=("e1",))
        repo.add(c1)
        c2 = Case(case_id=uuid.uuid4().hex, title="provider healthy", outcome="success",
                  features=(("kind", "restart"), ("env", "prod")), evidence_ids=("e2",))
        repo.add(c2)

        # Build knowledge
        knowledge = OperationalKnowledge()
        for c in repo.all():
            lesson = LessonExtractor.extract(c)
            knowledge.build_from_case(c, lesson)
        assert knowledge.index.count() == 2

        # Retrieval: query kemiripan provider restart prod
        query = _case(features=(("kind", "restart"), ("env", "prod")))
        retriever = CaseRetriever(repo)
        results = retriever.retrieve(query, limit=2)
        assert results

        # API + explainability + compliance
        api = KnowledgeAPI(knowledge=knowledge.index, cases=repo)
        assert api.knowledge_count() == 2
        entry = knowledge.index.all()[0]
        explainer = KnowledgeExplainer()
        expl = explainer.explain(entry, repo.all())
        assert expl.trace.evidence_ids

        # Compliance
        all_knowledge_have_evidence = all(
            e.evidence_ids for e in knowledge.index.all()
        )
        checker = KnowledgeComplianceChecker()
        assert checker.certify(all_have_evidence=all_knowledge_have_evidence)["certified"]
