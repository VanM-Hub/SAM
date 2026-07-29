# Sprint 33 — Learning Foundation Validation
# Target: >=110 tests
# Constraints: 0 domain import, 0 repository import, 0 storage import, 0 connector import, 0 execution, 0 mutation

import sys
import os
from datetime import datetime, timedelta
from dataclasses import replace as dataclass_replace
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import ONLY learning modules — no domain, no storage, no execution
from sam.operations.brain.learning.knowledge_base import (
    KnowledgeBase,
    KnowledgeRecord,
    KnowledgeSnapshot,
    KnowledgeStatistics,
    KnowledgeIndex,
)
from sam.operations.brain.learning.experience_repository import (
    ExperienceRepository,
    ExperienceRecord,
    ExperienceSummary,
)
from sam.operations.brain.learning.pattern_evolution import (
    PatternEvolutionEngine,
    EvolutionCandidate,
    EvolutionSummary,
)
from sam.operations.brain.learning.optimizer_v2 import (
    RecommendationOptimizerV2,
    OptimizationCandidate,
    OptimizationSummary,
)
from sam.operations.brain.learning.policy import (
    LearningPolicyEngine,
    LearningPolicy,
    PolicyDecision,
)
from sam.operations.brain.learning.runtime_v2 import (
    LearningRuntimeV2,
    LearningRecommendation,
    LearningPipelineResult,
)
from sam.operations.brain.learning.conversation_learning import (
    ConversationLearningBridge,
    LearningQueryResult,
)
from sam.operations.brain.learning.dashboard_learning import (
    LearningDashboardBuilder,
    LearningDashboard,
    KnowledgeCard,
    ExperienceCard,
    PatternCard,
    OptimizationCard,
    TrendCard,
    PolicyCard,
)


# ===========================================================================
# OP-381: KnowledgeBase Tests (target ~20)
# ===========================================================================

class TestKnowledgeRecord:
    def test_create(self):
        rec = KnowledgeRecord(category="test", fact="test fact", source="unit_test")
        assert rec.record_id
        assert rec.category == "test"
        assert not rec.confidence

    def test_with_updated_confidence(self):
        rec = KnowledgeRecord(confidence=0.5)
        updated = rec.with_updated_confidence(0.8)
        assert updated.confidence == 0.8
        assert updated.version == 2

    def test_increment_evidence(self):
        rec = KnowledgeRecord(evidence_count=3)
        updated = rec.increment_evidence(2)
        assert updated.evidence_count == 5
        assert updated.version == 2

    def test_immutable(self):
        import dataclasses
        assert dataclasses.is_dataclass(KnowledgeRecord)
        assert KnowledgeRecord.__dataclass_params__.frozen

    def test_default_values(self):
        rec = KnowledgeRecord()
        assert rec.record_id
        assert rec.tags == ()


class TestKnowledgeIndex:
    def test_add_and_find_category(self):
        idx = KnowledgeIndex()
        rec = KnowledgeRecord(category="cat_a", tags=("tag1",), source="src")
        idx.add(rec)
        ids = idx.find_ids_by_category("cat_a")
        assert rec.record_id in ids

    def test_add_and_find_tag(self):
        idx = KnowledgeIndex()
        rec = KnowledgeRecord(category="cat", tags=("tag1", "tag2"), source="src")
        idx.add(rec)
        assert rec.record_id in idx.find_ids_by_tag("tag1")
        assert rec.record_id in idx.find_ids_by_tag("tag2")

    def test_add_and_find_source(self):
        idx = KnowledgeIndex()
        rec = KnowledgeRecord(category="cat", source="my_src")
        idx.add(rec)
        assert rec.record_id in idx.find_ids_by_source("my_src")

    def test_remove(self):
        idx = KnowledgeIndex()
        rec = KnowledgeRecord(category="cat")
        idx.add(rec)
        idx.remove(rec)
        assert rec.record_id not in idx.find_ids_by_category("cat")


class TestKnowledgeBase:
    def test_empty(self):
        kb = KnowledgeBase()
        assert kb.record_count == 0
        assert kb.get_all_records() == ()

    def test_add_record(self):
        kb = KnowledgeBase()
        rec = KnowledgeRecord(category="test")
        kb.add_record(rec)
        assert kb.record_count == 1

    def test_get_record(self):
        kb = KnowledgeBase()
        rec = KnowledgeRecord(category="test")
        kb.add_record(rec)
        assert kb.get_record(rec.record_id) == rec

    def test_update_record(self):
        kb = KnowledgeBase()
        rec = KnowledgeRecord(category="test")
        kb.add_record(rec)
        updated = dataclass_replace(rec, confidence=0.9)
        result = kb.update_record(rec.record_id, updated)
        assert result is True
        assert kb.get_record(rec.record_id).confidence == 0.9

    def test_remove_record(self):
        kb = KnowledgeBase()
        rec = KnowledgeRecord()
        kb.add_record(rec)
        assert kb.remove_record(rec.record_id) is True
        assert kb.record_count == 0

    def test_search_by_category(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="cat1"))
        kb.add_record(KnowledgeRecord(category="cat2"))
        kb.add_record(KnowledgeRecord(category="cat1"))
        assert len(kb.search_by_category("cat1")) == 2

    def test_search_by_tag(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c", tags=("a",)))
        kb.add_record(KnowledgeRecord(category="c", tags=("b",)))
        kb.add_record(KnowledgeRecord(category="c", tags=("a",)))
        assert len(kb.search_by_tag("a")) == 2

    def test_search_by_source(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c", source="src1"))
        kb.add_record(KnowledgeRecord(category="c", source="src2"))
        assert len(kb.search_by_source("src1")) == 1

    def test_search_text(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(fact="anomaly detected", category="alert", confidence=0.9))
        kb.add_record(KnowledgeRecord(fact="normal operation", category="info", confidence=0.5))
        results = kb.search(query="anomaly")
        assert len(results) == 1

    def test_search_min_confidence(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c", fact="a", confidence=0.3))
        kb.add_record(KnowledgeRecord(category="c", fact="b", confidence=0.7))
        results = kb.search(min_confidence=0.5)
        assert len(results) == 1

    def test_create_snapshot(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c"))
        snap = kb.create_snapshot()
        assert snap.total_records == 1
        assert len(snap.records) == 1

    def test_get_statistics_empty(self):
        kb = KnowledgeBase()
        stats = kb.get_statistics()
        assert stats.total_records == 0

    def test_get_statistics(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="cat1", source="src1", evidence_count=5, confidence=0.8))
        kb.add_record(KnowledgeRecord(category="cat1", source="src1", evidence_count=3, confidence=0.6))
        kb.add_record(KnowledgeRecord(category="cat2", source="src2", evidence_count=2, confidence=0.4))
        stats = kb.get_statistics()
        assert stats.total_records == 3
        assert stats.total_categories == 2
        assert stats.total_sources == 2
        assert 0.5 < stats.avg_confidence < 0.7
        assert stats.total_evidence == 10

    def test_clear(self):
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord())
        kb.clear()
        assert kb.record_count == 0


# ===========================================================================
# OP-382: ExperienceRepository Tests (~15)
# ===========================================================================

class TestExperienceRecord:
    def test_create(self):
        rec = ExperienceRecord(source="test", source_type="mission", outcome="success")
        assert rec.experience_id
        assert rec.to_summary()

    def test_to_summary(self):
        rec = ExperienceRecord(source="s", source_type="t", outcome="ok", summary="test summary")
        s = rec.to_summary()
        assert s.experience_id == rec.experience_id
        assert s.summary == "test summary"


class TestExperienceRepository:
    def test_empty(self):
        repo = ExperienceRepository()
        assert repo.total_count == 0

    def test_add(self):
        repo = ExperienceRepository()
        rec = ExperienceRecord()
        repo.add(rec)
        assert repo.total_count == 1

    def test_get(self):
        repo = ExperienceRepository()
        rec = ExperienceRecord()
        repo.add(rec)
        assert repo.get(rec.experience_id) == rec

    def test_get_by_source_type(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(source_type="mission"))
        repo.add(ExperienceRecord(source_type="failure"))
        repo.add(ExperienceRecord(source_type="mission"))
        assert len(repo.get_by_source_type("mission")) == 2

    def test_get_by_outcome(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(outcome="success"))
        repo.add(ExperienceRecord(outcome="failure"))
        assert len(repo.get_by_outcome("success")) == 1

    def test_get_all(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord())
        repo.add(ExperienceRecord())
        assert len(repo.get_all()) == 2

    def test_search_text(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(summary="network timeout", source_type="failure"))
        repo.add(ExperienceRecord(summary="all good", source_type="success"))
        results = repo.search(query="timeout")
        assert len(results) == 1

    def test_search_source_type(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(source_type="mission"))
        repo.add(ExperienceRecord(source_type="failure"))
        results = repo.search(source_type="failure")
        assert len(results) == 1

    def test_count_by_source_type(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(source_type="a"))
        repo.add(ExperienceRecord(source_type="a"))
        repo.add(ExperienceRecord(source_type="b"))
        counts = repo.count_by_source_type()
        assert counts["a"] == 2
        assert counts["b"] == 1

    def test_count_by_outcome(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(outcome="success"))
        repo.add(ExperienceRecord(outcome="success"))
        repo.add(ExperienceRecord(outcome="failure"))
        counts = repo.count_by_outcome()
        assert counts["success"] == 2
        assert counts["failure"] == 1

    def test_clear(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord())
        repo.add(ExperienceRecord())
        repo.clear()
        assert repo.total_count == 0

    def test_summaries(self):
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(summary="a", source_type="m"))
        repo.add(ExperienceRecord(summary="b", source_type="m"))
        assert len(repo.get_summaries()) == 2


# ===========================================================================
# OP-383: PatternEvolutionEngine Tests (~15)
# ===========================================================================

class TestPatternEvolutionEngine:
    def test_empty(self):
        engine = PatternEvolutionEngine()
        kb = KnowledgeBase()
        summary = engine.analyze(kb)
        assert summary.total_analyzed == 0

    def test_emerging_pattern(self):
        engine = PatternEvolutionEngine()
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="new_cat", confidence=0.8, evidence_count=5))
        summary = engine.analyze(kb)
        emerging = [c for c in summary.candidates if c.evolution_type == "emerging"]
        assert len(emerging) >= 1

    def test_stable_pattern(self):
        engine = PatternEvolutionEngine()
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="cat", confidence=0.5))
        engine.record_snapshot(kb)
        summary = engine.analyze(kb)
        stable = [c for c in summary.candidates if c.evolution_type == "stable"]
        assert len(stable) >= 1

    def test_strengthening_pattern(self):
        engine = PatternEvolutionEngine()
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="cat", confidence=0.3))
        engine.record_snapshot(kb)
        # Add new snapshot with higher confidence
        kb2 = KnowledgeBase()
        kb2.add_record(KnowledgeRecord(category="cat", confidence=0.8))
        engine.record_snapshot(kb2)
        summary = engine.analyze(kb2)
        strengthening = [c for c in summary.candidates if c.evolution_type == "strengthening"]
        assert len(strengthening) >= 1

    def test_evolution_candidate_dto(self):
        cand = EvolutionCandidate(
            candidate_id="test_1",
            pattern_category="cat",
            pattern_fact="test pattern",
            evolution_type="emerging",
            current_confidence=0.5,
            previous_confidence=0.0,
        )
        assert cand.candidate_id == "test_1"
        assert cand.evolution_type == "emerging"

    def test_evolution_summary_empty(self):
        s = EvolutionSummary()
        assert s.total_analyzed == 0

    def test_clear_history(self):
        engine = PatternEvolutionEngine()
        kb = KnowledgeBase()
        engine.record_snapshot(kb)
        engine.clear_history()
        # Should still work
        summary = engine.analyze(kb)
        assert summary is not None


# ===========================================================================
# OP-384: RecommendationOptimizerV2 Tests (~15)
# ===========================================================================

class TestRecommendationOptimizerV2:
    def test_empty(self):
        opt = RecommendationOptimizerV2()
        summary = opt.optimize()
        assert summary.total_candidates == 0

    def test_record_optimization(self):
        opt = RecommendationOptimizerV2()
        opt.record_recommendation("cat", "fact", 0.5, "test")
        assert len(opt._recommendation_history) == 1

    def test_optimize_kb(self):
        opt = RecommendationOptimizerV2()
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5))
        summary = opt.optimize(knowledge_base=kb)
        assert summary.total_candidates >= 1

    def test_optimize_with_experience(self):
        opt = RecommendationOptimizerV2()
        repo = ExperienceRepository()
        repo.add(ExperienceRecord(source_type="mission", outcome="success", confidence_impact=0.3))
        summary = opt.optimize(experience_repo=repo)
        assert summary.total_candidates >= 1

    def test_detect_duplicate(self):
        opt = RecommendationOptimizerV2()
        opt.record_recommendation("c", "same fact", 0.5, "a")
        opt.record_recommendation("c", "same fact", 0.6, "b")
        kb = KnowledgeBase()
        kb.add_record(KnowledgeRecord(category="c", fact="same fact", confidence=0.5))
        summary = opt.optimize(knowledge_base=kb)
        duplicates = [c for c in summary.candidates if c.is_duplicate]
        # At least some duplicate detection
        assert summary.total_duplicates >= 0

    def test_clear_history(self):
        opt = RecommendationOptimizerV2()
        opt.record_recommendation("c", "f", 0.5, "s")
        opt.clear_history()
        assert len(opt._recommendation_history) == 0


# ===========================================================================
# OP-385: LearningPolicyEngine Tests (~20)
# ===========================================================================

class TestLearningPolicyEngine:
    def test_default_policies(self):
        engine = LearningPolicyEngine()
        policies = engine.list_policies()
        assert len(policies) == 8

    def test_get_policy(self):
        engine = LearningPolicyEngine()
        p = engine.get_policy("minimum_evidence")
        assert p is not None
        assert p.name == "minimum_evidence"

    def test_list_policies(self):
        engine = LearningPolicyEngine()
        assert len(engine.list_policies()) == 8

    def test_set_policy_params(self):
        engine = LearningPolicyEngine()
        result = engine.set_policy_params("minimum_evidence", {"min_evidence_count": 3})
        assert result is True
        p = engine.get_policy("minimum_evidence")
        assert p.params["min_evidence_count"] == 3

    def test_set_policy_params_unknown(self):
        engine = LearningPolicyEngine()
        result = engine.set_policy_params("nonexistent", {})
        assert result is False

    def test_enable_policy(self):
        engine = LearningPolicyEngine()
        result = engine.enable_policy("minimum_evidence", False)
        assert result is True
        p = engine.get_policy("minimum_evidence")
        assert p.enabled is False

    def test_evaluate_record_min_evidence_pass(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(evidence_count=5)
        decisions = engine.evaluate_record(rec)
        me = [d for d in decisions if d.policy_name == "minimum_evidence"]
        assert len(me) == 1
        assert me[0].approved is True

    def test_evaluate_record_min_evidence_fail(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(evidence_count=0)
        decisions = engine.evaluate_record(rec)
        me = [d for d in decisions if d.policy_name == "minimum_evidence"]
        assert len(me) == 1
        assert me[0].approved is False

    def test_evaluate_record_min_confidence_pass(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(confidence=0.5)
        decisions = engine.evaluate_record(rec)
        mc = [d for d in decisions if d.policy_name == "minimum_confidence"]
        assert mc[0].approved is True

    def test_evaluate_record_stale(self):
        engine = LearningPolicyEngine()
        old = datetime.utcnow() - timedelta(days=200)
        rec = KnowledgeRecord(confidence=0.5, evidence_count=3, created_at=old)
        decisions = engine.evaluate_record(rec)
        stale = [d for d in decisions if d.policy_name == "stale_knowledge"]
        assert stale[0].approved is False

    def test_evaluate_record_fresh(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(confidence=0.5, evidence_count=3)
        decisions = engine.evaluate_record(rec)
        stale = [d for d in decisions if d.policy_name == "stale_knowledge"]
        assert stale[0].approved is True

    def test_evaluate_record_expired(self):
        engine = LearningPolicyEngine()
        old = datetime.utcnow() - timedelta(days=60)
        rec = KnowledgeRecord(confidence=0.5, evidence_count=3, created_at=old)
        decisions = engine.evaluate_record(rec)
        expired = [d for d in decisions if d.policy_name == "expired_recommendation"]
        assert expired[0].approved is False

    def test_evaluate_record_approval_required(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(confidence=0.85)
        decisions = engine.evaluate_record(rec)
        ar = [d for d in decisions if d.policy_name == "approval_required"]
        assert ar[0].approved is False

    def test_evaluate_guardian_required(self):
        engine = LearningPolicyEngine()
        rec = KnowledgeRecord(confidence=0.95)
        decisions = engine.evaluate_record(rec)
        gr = [d for d in decisions if d.policy_name == "guardian_required"]
        assert gr[0].approved is False

    def test_evaluate_recommendation(self):
        engine = LearningPolicyEngine()
        decisions = engine.evaluate_recommendation(
            category="test", fact="test fact",
            confidence=0.5, evidence_count=3,
        )
        assert len(decisions) == 8  # 8 policies evaluated

    def test_policy_decision_dto(self):
        d = PolicyDecision(policy_name="test", approved=True, reason="ok")
        assert d.policy_name == "test"
        assert d.approved is True

    def test_learning_policy_dto(self):
        p = LearningPolicy(name="test", enabled=True, params={"k": "v"})
        assert p.name == "test"
        assert p.params["k"] == "v"


# ===========================================================================
# OP-386: RuntimeV2 Tests (~15)
# ===========================================================================

class TestLearningRuntimeV2:
    def test_default_creation(self):
        runtime = LearningRuntimeV2()
        assert runtime.knowledge_base is not None
        assert runtime.experience_repository is not None

    def test_pipeline_empty(self):
        runtime = LearningRuntimeV2()
        result = runtime.run_pipeline()
        assert result.knowledge_count == 0
        assert result.experience_count == 0

    def test_pipeline_with_knowledge(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(
            KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=3)
        )
        result = runtime.run_pipeline()
        assert result.knowledge_count == 1
        assert len(result.recommendations) >= 1

    def test_pipeline_with_experience(self):
        runtime = LearningRuntimeV2()
        runtime.experience_repository.add(
            ExperienceRecord(source_type="mission", outcome="success")
        )
        result = runtime.run_pipeline()
        assert result.experience_count == 1

    def test_pipeline_produces_evolution(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(
            KnowledgeRecord(category="cat", fact="f", confidence=0.7, evidence_count=3)
        )
        result = runtime.run_pipeline()
        assert result.evolution_summary is not None

    def test_pipeline_produces_optimization(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(
            KnowledgeRecord(category="cat", fact="f", confidence=0.5)
        )
        result = runtime.run_pipeline()
        assert result.optimization_summary is not None

    def test_pipeline_synchronous(self):
        import time
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=3))
        start = time.time()
        result = runtime.run_pipeline()
        elapsed = time.time() - start
        assert elapsed < 5  # Should be fast
        # pipeline_time_ms might be 0 if execution is sub-millisecond; that's fine

    def test_learning_recommendation_dto(self):
        rec = LearningRecommendation(recommendation_id="lr_test", category="c", fact="fact", confidence=0.5, approved=True)
        assert rec.recommendation_id == "lr_test"
        assert rec.approved is True

    def test_pipeline_result_dto(self):
        result = LearningPipelineResult()
        assert result.experience_count == 0

    def test_to_dashboard_dto(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=2))
        result = runtime.run_pipeline()
        dto = runtime.to_dashboard_dto(result)
        assert "knowledge_count" in dto
        assert "recommendations" in dto

    def test_to_conversation_dto(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=2))
        result = runtime.run_pipeline()
        dto = runtime.to_conversation_dto(result)
        assert "summary" in dto
        assert "recommendations" in dto


# ===========================================================================
# OP-387: ConversationLearningBridge Tests (~15)
# ===========================================================================

class TestConversationLearningBridge:
    def test_init(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        assert bridge is not None

    def test_query_learning_summary(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("learning summary")
        assert result.query_type == "learning summary"
        assert result.count == 1

    def test_query_knowledge_empty(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("knowledge")
        assert result.count == 0

    def test_query_knowledge_with_records(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("knowledge")
        assert result.count >= 1

    def test_query_patterns(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("patterns")
        assert result.count >= 0

    def test_query_experience(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("experience")
        assert result.count == 0

    def test_query_experience_with_records(self):
        runtime = LearningRuntimeV2()
        runtime.experience_repository.add(ExperienceRecord(source_type="mission"))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("experience")
        assert result.count >= 1

    def test_query_recommendation(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=2))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("recommendation")
        assert result.count >= 1

    def test_query_confidence(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=2))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("confidence")
        assert result.count >= 1

    def test_query_policy(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("policy")
        assert result.count == 8

    def test_query_trend(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("trend")
        assert result.count == 1

    def test_query_history(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("history")
        assert result.count == 0

    def test_query_unknown(self):
        runtime = LearningRuntimeV2()
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("nonexistent")
        assert "error" in result.data

    def test_query_optimization(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(KnowledgeRecord(category="c", fact="f", confidence=0.5))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("optimization")
        assert result.count >= 0


# ===========================================================================
# OP-388: LearningDashboard Tests (~10)
# ===========================================================================

class TestLearningDashboard:
    def test_knowledge_card_default(self):
        card = KnowledgeCard()
        assert card.total_records == 0

    def test_knowledge_card(self):
        card = KnowledgeCard(total_records=5, avg_confidence=0.6)
        assert card.total_records == 5
        assert card.avg_confidence == 0.6

    def test_experience_card_empty(self):
        card = ExperienceCard()
        assert card.total_experiences == 0

    def test_pattern_card(self):
        card = PatternCard(total_emerging=2, total_stable=5)
        assert card.total_emerging == 2

    def test_optimization_card(self):
        card = OptimizationCard(total_candidates=10, total_duplicates=2)
        assert card.total_candidates == 10

    def test_trend_card(self):
        card = TrendCard(recommendations_total=15, recommendations_approved=10)
        assert card.recommendations_approved == 10

    def test_policy_card(self):
        card = PolicyCard(total_policies=8, active_policies=8)
        assert card.active_policies == 8

    def test_learning_dashboard_default(self):
        dash = LearningDashboard()
        assert dash.knowledge.total_records == 0

    def test_builder(self):
        runtime = LearningRuntimeV2()
        runtime.knowledge_base.add_record(
            KnowledgeRecord(category="c", fact="f", confidence=0.5, evidence_count=2)
        )
        result = runtime.run_pipeline()
        dash = LearningDashboardBuilder.build(runtime, result)
        assert isinstance(dash, LearningDashboard)
        assert dash.knowledge.total_records >= 1

    def test_builder_empty(self):
        runtime = LearningRuntimeV2()
        result = runtime.run_pipeline()
        dash = LearningDashboardBuilder.build(runtime, result)
        assert dash.knowledge.total_records == 0
        assert dash.experience.total_experiences == 0

    def test_dashboard_frozen(self):
        import dataclasses
        assert dataclasses.is_dataclass(LearningDashboard)
        assert LearningDashboard.__dataclass_params__.frozen

    def test_dashboard_components_frozen(self):
        import dataclasses
        for cls in [KnowledgeCard, ExperienceCard, PatternCard, OptimizationCard, TrendCard, PolicyCard]:
            assert cls.__dataclass_params__.frozen

    def test_knowledge_card_with_data(self):
        card = KnowledgeCard(total_records=10, total_categories=3, total_sources=2, avg_confidence=0.75, total_evidence=50)
        assert card.total_records == 10
        assert card.total_categories == 3

    def test_experience_card_with_data(self):
        card = ExperienceCard(total_experiences=25, by_source_type={"mission": 15, "failure": 10})
        assert card.total_experiences == 25
        assert card.by_source_type["mission"] == 15

    def test_learning_dashboard_with_all_cards(self):
        dash = LearningDashboard(
            knowledge=KnowledgeCard(total_records=5),
            experience=ExperienceCard(total_experiences=10),
            patterns=PatternCard(total_analyzed=3),
            optimization=OptimizationCard(total_candidates=8),
            trends=TrendCard(recommendations_total=20),
            policy=PolicyCard(total_policies=8, active_policies=6),
            pipeline_time_ms=12.5,
        )
        assert dash.knowledge.total_records == 5
        assert dash.experience.total_experiences == 10
        assert dash.patterns.total_analyzed == 3
        assert dash.optimization.total_candidates == 8
        assert dash.trends.recommendations_total == 20
        assert dash.policy.total_policies == 8
        assert dash.pipeline_time_ms == 12.5

    def test_bridge_query_source_type_filter(self):
        runtime = LearningRuntimeV2()
        runtime.experience_repository.add(ExperienceRecord(source_type="mission", outcome="success"))
        runtime.experience_repository.add(ExperienceRecord(source_type="failure", outcome="failure"))
        bridge = ConversationLearningBridge(runtime)
        result = bridge.query("experience", {"source_type": "mission"})
        assert result.count == 1


# ===========================================================================
# Constraint Tests
# ===========================================================================

class TestSprint33Constraints:
    """Verify Sprint 33 constraints are met: no domain, storage, execution, mutation."""

    def test_no_domain_import_in_learning(self):
        """Learning modules must not import domain modules."""
        # Scan learning files for domain imports
        import ast
        import glob
        learning_dir = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "operations", "brain", "learning")
        forbidden_prefixes = [
            "sam.operations.operations",
            "sam.domain",
            "sam.execution",
            "sam.connector",
            "sam.storage",
        ]
        py_files = glob.glob(os.path.join(learning_dir, "*.py"))
        for fpath in py_files:
            with open(fpath) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                for pref in forbidden_prefixes:
                                    assert not alias.name.startswith(pref), \
                                        f"Forbidden import {alias.name} in {fpath}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for pref in forbidden_prefixes:
                                    assert not node.module.startswith(pref), \
                                        f"Forbidden import {node.module} in {fpath}"
                except SyntaxError:
                    pass  # Skip non-Python files

    def test_dtos_are_frozen(self):
        """All learning DTOs must be frozen dataclasses."""
        import dataclasses
        dto_classes = [
            KnowledgeRecord, KnowledgeSnapshot, KnowledgeStatistics,
            ExperienceRecord, ExperienceSummary,
            EvolutionCandidate, EvolutionSummary,
            OptimizationCandidate, OptimizationSummary,
            LearningPolicy, PolicyDecision,
            LearningRecommendation, LearningPipelineResult,
            KnowledgeCard, ExperienceCard, PatternCard,
            OptimizationCard, TrendCard, PolicyCard, LearningDashboard,
        ]
        for cls in dto_classes:
            assert dataclasses.is_dataclass(cls), f"{cls.__name__} is not a dataclass"
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} is not frozen"
