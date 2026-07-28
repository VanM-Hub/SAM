"""
Sprint 21 Ã¢â‚¬â€ Learning & Optimization Tests.
OP-261 through OP-268.
"""
from __future__ import annotations
import time
import pytest

# -- OP-261 Pattern Miner --
from sam.operations.brain.pattern_miner import (
    PatternMiner, OperationalRecord, PatternDiscoveryResult,
    build_record, discover_patterns,
)

class TestPatternMiner:
    def test_discover_no_records(self):
        miner = PatternMiner()
        result = miner.discover([])
        assert isinstance(result, PatternDiscoveryResult)
        assert result.patterns == []
        assert result.records_scanned == 0

    def test_discover_source_failure(self):
        records = [
            build_record("r1", "execution", "test", source="svc_a", outcome="failure"),
            build_record("r2", "execution", "test", source="svc_a", outcome="failure"),
            build_record("r3", "execution", "test", source="svc_a", outcome="failure"),
            build_record("r4", "execution", "test", source="svc_a", outcome="failure"),
        ]
        result = discover_patterns(records, time_window_hours=1000)
        patterns = {p.pattern_type: p for p in result.patterns}
        assert "source_failure" in patterns

    def test_severity_pattern(self):
        records = [build_record(f"r{i}", "finding", "alert", severity="critical") for i in range(10)]
        result = discover_patterns(records)
        sev = [p for p in result.patterns if p.pattern_type == "severity"]
        assert len(sev) >= 1

    def test_result_to_dict(self):
        result = discover_patterns([])
        assert isinstance(result.to_dict_list(), list)

# -- OP-262 Success Estimator --
from sam.operations.brain.success_estimator import (
    SuccessEstimator, SuccessEstimate, EvidencePiece,
    HistoricalOutcome, estimate_success, EstimatorConfig,
)

class TestSuccessEstimator:
    def test_estimate_range(self):
        est = SuccessEstimator()
        result = est.estimate("rec-1")
        assert 0.0 <= result.probability <= 1.0

    def test_historical_boost(self):
        est = SuccessEstimator()
        for _ in range(3):
            est.add_outcome(HistoricalOutcome("r", "recommendation", title="fix", success=True))
        result = est.estimate("rec-d", title="fix")
        assert result.probability > 0.5

    def test_high_risk_low_prob(self):
        low = SuccessEstimator().estimate("rl", risk_score=0.1)
        high = SuccessEstimator().estimate("rh", risk_score=0.9)
        assert low.probability >= high.probability

# -- OP-263 Optimizer --
from sam.operations.brain.optimizer import RecommendationOptimizer, OptimizationReport

class TestOptimizer:
    def test_no_outcomes_unchanged(self):
        opt = RecommendationOptimizer()
        assert opt.optimize("r", 0.5).direction == "unchanged"

    def test_success_boost(self):
        opt = RecommendationOptimizer()
        for _ in range(5):
            opt.record_outcome("r2", True)
        assert opt.optimize("r2", 0.5).direction == "increase"

    def test_failure_penalty(self):
        opt = RecommendationOptimizer()
        for _ in range(5):
            opt.record_outcome("r3", False)
        assert opt.optimize("r3", 0.7).direction == "decrease"

    def test_batch_report(self):
        opt = RecommendationOptimizer()
        opt.record_outcomes({"a": [True]*3, "b": [False]*3})
        report = opt.optimize_batch({"a": 0.5, "b": 0.7})
        assert report.total_adjusted > 0

# -- OP-264 Feedback Collector --
from sam.operations.brain.feedback_collector import FeedbackCollector, FeedbackEvent

class TestFeedbackCollector:
    def test_empty(self):
        assert FeedbackCollector().summarize().total_events == 0

    def test_add_events(self):
        fc = FeedbackCollector()
        fc.add_approval("p1", True)
        fc.add_execution("m1", True)
        fc.add_anomaly("crash")
        fc.add_health_score(0.9)
        assert fc.summarize().total_events >= 4

    def test_clear(self):
        fc = FeedbackCollector()
        fc.add_approval("p", True)
        assert fc.clear() == 1

# -- OP-265 Learning Pipeline --
from sam.operations.brain.learning_pipeline import LearningPipeline, KnowledgeSnapshot

class TestLearningPipeline:
    def test_empty_run(self):
        result = LearningPipeline().run()
        assert hasattr(result, "patterns")

    def test_snapshot_increments(self):
        pipe = LearningPipeline()
        pipe.run()
        v1 = pipe.snapshot()
        v2 = pipe.snapshot()
        assert v1.version_id != v2.version_id

    def test_apply_feedback(self):
        pipe = LearningPipeline()
        pipe.apply_feedback([FeedbackEvent("e1", "approval", time.time(), value=1.0, outcome="approved")])
        result = pipe.run()
        assert result.feedback_summary.total_events >= 1

# -- OP-266 Dashboard Brain --
from sam.operations.brain.dashboard_brain import DashboardBrainV2, compute_dashboard

class TestDashboardBrain:
    def test_compute(self):
        assert DashboardBrainV2().compute(health_score=1.0).health_score == 1.0

    def test_insight_generation(self):
        brain = DashboardBrainV2()
        brain.compute(health_score=0.9, approval_rate=0.8)
        brain.compute(health_score=0.7, approval_rate=0.5)
        state = brain.compute(health_score=0.5, approval_rate=0.3, mission_success_rate=0.4)
        assert len(state.insights) >= 1

# -- OP-267 Integration --
from sam.operations.brain.integration21 import LearningIntegration

class TestIntegration21:
    def test_run_empty(self):
        assert hasattr(LearningIntegration().run(), "learning")

    def test_with_records(self):
        integration = LearningIntegration()
        records = [
            build_record("r1", "execution", "test", source="svc", outcome="failure"),
            build_record("r2", "execution", "test", source="svc", outcome="success"),
        ]
        result = integration.run(operational_records=records, approval_rate=0.5, mission_success_rate=0.8)
        assert result.knowledge.version_id != ""
        assert result.dashboard.health_score > 0

# -- OP-268 Validation --
from sam.operations.brain.validation21 import Sprint21Validator, Sprint21ValidationResult, validate_sprint21

class TestSprint21Validation:
    def test_validate_clean(self):
        validator = Sprint21Validator()
        clean = "from __future__ import annotations\nfrom dataclasses import dataclass\nx = 1\n"
        result = validator.validate(modules=["test.clean"], source_paths={"test.clean": clean})
        assert result.passed

    def test_detects_forbidden(self):
        validator = Sprint21Validator()
        bad = "import torch\nimport sklearn\n"
        result = validator.validate(modules=["test.bad"], source_paths={"test.bad": bad})
        assert not result.checks["no_forbidden_imports"]

    def test_convenience(self):
        result = validate_sprint21(["sam.operations.brain.validation21"])
        assert isinstance(result, Sprint21ValidationResult)