"""Test IP-4.3-003 - Continuous Learning (MISSION-4.3).

Coverage: WP-21..WP-30 - recommendation feedback/improvement, learning
evaluation, experience verification, knowledge validation, metrics, API,
compliance, end-to-end.
"""
import os
import sys
import uuid


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_learning.persistent_storage import (
    PersistenceEngine,
    StorageConfig,
)
from sam.operational_learning.recommendation_feedback import (
    RecommendationFeedback,
    RecommendationFeedbackStore,
)
from sam.operational_learning.recommendation_improvement import (
    RecommendationImprover,
)
from sam.operational_learning.learning_evaluation import (
    ExperienceVerifier,
    LearningEvaluator,
)
from sam.operational_learning.knowledge_validation import (
    KnowledgeValidator,
)
from sam.operational_learning.operational_knowledge import (
    KnowledgeEntry,
    KnowledgeIndex,
)
from sam.operational_learning.operational_metrics import (
    LearningMetricsCalculator,
)
from sam.operational_learning.learning_api import LearningAPI
from sam.operational_learning.learning_compliance import (
    LearningComplianceChecker,
)


def _fb_engine(tmp_path):
    return PersistenceEngine(StorageConfig(base_dir=str(tmp_path), collection="feedback"))


# ---------------------------------------------------------------------------
# WP-21 Recommendation Feedback
# ---------------------------------------------------------------------------

class TestRecommendationFeedback:
    def test_add_and_retrieve(self, tmp_path):
        store = RecommendationFeedbackStore(_fb_engine(tmp_path))
        fb = RecommendationFeedback(
            feedback_id=uuid.uuid4().hex, recommendation_id="rec-1", rating=0.8
        )
        store.add(fb)
        assert store.get(fb.feedback_id).rating == 0.8

    def test_for_recommendation(self, tmp_path):
        store = RecommendationFeedbackStore(_fb_engine(tmp_path))
        store.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r1", rating=0.5))
        store.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r1", rating=-0.5))
        store.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r2", rating=0.9))
        assert len(store.for_recommendation("r1")) == 2

    def test_counts_and_persistent(self, tmp_path):
        path = str(tmp_path)
        s1 = RecommendationFeedbackStore(PersistenceEngine(StorageConfig(base_dir=path, collection="feedback")))
        s1.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r1", rating=0.1))
        s2 = RecommendationFeedbackStore(PersistenceEngine(StorageConfig(base_dir=path, collection="feedback")))
        assert s2.count() == 1


# ---------------------------------------------------------------------------
# WP-22 Recommendation Improvement
# ---------------------------------------------------------------------------

class TestRecommendationImprovement:
    def test_positive_feedback_raises_priority(self, tmp_path):
        store = RecommendationFeedbackStore(_fb_engine(tmp_path))
        store.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r1", rating=0.9))
        store.add(RecommendationFeedback(feedback_id=uuid.uuid4().hex, recommendation_id="r1", rating=0.8))
        improver = RecommendationImprover(store)
        adj = improver.improve("r1", "normal")
        assert adj.adjusted_priority == "high"
        assert adj.feedback_samples == 2

    def test_no_feedback_no_change(self, tmp_path):
        store = RecommendationFeedbackStore(_fb_engine(tmp_path))
        improver = RecommendationImprover(store)
        adj = improver.improve("r1", "high")
        assert adj.adjusted_priority == "high"
        assert adj.feedback_samples == 0


# ---------------------------------------------------------------------------
# WP-23 Learning Evaluation
# ---------------------------------------------------------------------------

class TestLearningEvaluation:
    def test_evaluate_rating(self):
        eval_result = LearningEvaluator.evaluate(
            "e1", knowledge_count=3, case_count=2, feedback_count=2, total_rating=1.0
        )
        assert eval_result.rating == 0.5
        assert eval_result.is_learning

    def test_no_learning_when_empty(self):
        eval_result = LearningEvaluator.evaluate(
            "e2", knowledge_count=0, case_count=0, feedback_count=0
        )
        assert not eval_result.is_learning


# ---------------------------------------------------------------------------
# WP-24 Experience Verification
# ---------------------------------------------------------------------------

class TestExperienceVerification:
    def test_verify_clean(self):
        out = ExperienceVerifier.verify("exp-1")
        assert out.verified is True
        assert out.method == "integrity"

    def test_verify_mutation_detected(self):
        out = ExperienceVerifier.verify("exp-1", immutable=False)
        assert not out.verified

    def test_verify_no_evidence(self):
        out = ExperienceVerifier.verify("exp-1", has_evidence=False)
        assert not out.verified


# ---------------------------------------------------------------------------
# WP-25 Knowledge Validation
# ---------------------------------------------------------------------------

class TestKnowledgeValidation:
    def test_validate_valid(self):
        entry = KnowledgeEntry(
            knowledge_id="k1", title="t", content="c",
            evidence_ids=("e1",), confidence=0.8,
        )
        validator = KnowledgeValidator()
        result = validator.validate(entry)
        assert result.valid is True

    def test_validate_missing_evidence(self):
        entry = KnowledgeEntry(knowledge_id="k2", title="t", content="c", confidence=0.8)
        assert not KnowledgeValidator().validate(entry).valid

    def test_validate_low_confidence(self):
        entry = KnowledgeEntry(
            knowledge_id="k3", title="t", content="c", evidence_ids=("e1",), confidence=0.1
        )
        assert not KnowledgeValidator().validate(entry).valid


# ---------------------------------------------------------------------------
# WP-26 Operational Metrics
# ---------------------------------------------------------------------------

class TestOperationalMetrics:
    def test_calculate_rates(self):
        metrics = LearningMetricsCalculator.calculate(
            total_experiences=10, total_cases=5, total_knowledge=4,
            total_feedback=3, validated_knowledge=3,
        )
        assert metrics.learning_rate == 0.4
        assert metrics.validation_rate == 0.75


# ---------------------------------------------------------------------------
# WP-27 Learning API
# ---------------------------------------------------------------------------

class TestLearningAPI:
    def test_submit_feedback_and_summary(self, tmp_path):
        knowledge = KnowledgeIndex()
        knowledge.add(KnowledgeEntry(knowledge_id="k1", title="t", content="c", evidence_ids=("e1",), confidence=0.8))
        store = RecommendationFeedbackStore(_fb_engine(tmp_path))
        api = LearningAPI(knowledge=knowledge, feedback=store, experience_count=2, case_count=1)
        api.submit_feedback("rec-1", 0.7)
        api.submit_feedback("rec-1", 0.9)
        summary = api.summary()
        assert summary["feedback_count"] == 2
        assert summary["knowledge_count"] == 1
        assert summary["evaluation"]["rating"] == 0.8


# ---------------------------------------------------------------------------
# WP-28 Learning Compliance
# ---------------------------------------------------------------------------

class TestLearningCompliance:
    def test_certify_clean(self):
        checker = LearningComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_execution(self):
        assert not LearningComplianceChecker().certify(execution=True)["certified"]

    def test_detects_approval(self):
        assert not LearningComplianceChecker().certify(approval=True)["certified"]

    def test_detects_authority_leakage(self):
        assert not LearningComplianceChecker().certify(authority_leakage=True)["certified"]


# ---------------------------------------------------------------------------
# WP-29/30 End-to-End + Baseline
# ---------------------------------------------------------------------------

class TestContinuousLearningEndToEnd:
    def test_end_to_end_learning(self, tmp_path):
        path = str(tmp_path)

        # Knowledge
        knowledge = KnowledgeIndex()
        knowledge.add(KnowledgeEntry(knowledge_id="k1", title="restart helps", content="restart", evidence_ids=("e1",), confidence=0.9))
        knowledge.add(KnowledgeEntry(knowledge_id="k2", title="grow memory", content="grow", evidence_ids=("e2",), confidence=0.5))

        # Feedback
        store = RecommendationFeedbackStore(PersistenceEngine(StorageConfig(base_dir=path, collection="feedback")))
        api = LearningAPI(knowledge=knowledge, feedback=store, experience_count=5, case_count=3)
        api.submit_feedback("rec-restart", 0.9)
        api.submit_feedback("rec-restart", 1.0)

        # Improvement pakai feedback
        improver = RecommendationImprover(store)
        adj = improver.improve("rec-restart", "normal")
        assert adj.adjusted_priority == "high"

        # Validation
        validator = KnowledgeValidator()
        validations = validator.validate_many(knowledge.all())
        assert all(v.valid for v in validations)

        # Evaluation + metrics
        eval_result = LearningEvaluator.evaluate(
            "e", knowledge_count=knowledge.count(), case_count=3,
            feedback_count=api.feedback_count(), total_rating=1.9,
        )
        assert eval_result.is_learning
        metrics = LearningMetricsCalculator.calculate(
            total_experiences=5, total_cases=3, total_knowledge=2,
            total_feedback=2, validated_knowledge=2,
        )
        assert metrics.learning_rate > 0

        # Compliance penuh
        checker = LearningComplianceChecker()
        cert = checker.certify()
        assert cert["certified"] is True
        assert checker.check(evidence_based=False).passed is False
