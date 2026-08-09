"""Test MISSION-5.6 - Adaptive Governance (IP-5.6-001..005).

Coverage: WP-01..WP-70 - learning, effectiveness, simulation, impact,
recommendation, evolution workspace, certification. Authority tetap di manusia.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.adaptive_governance import (
    AdaptiveCertStatus,
    AdaptiveGovernanceCertification,
    ApprovalContextBuilder,
    EffectivenessAnalyzer,
    ExperienceSample,
    GovernanceChangeProposal,
    GovernanceEvolutionWorkspace,
    ImpactAnalyzer,
    ImpactSeverity,
    ImpactTarget,
    LearningComplianceChecker,
    LearningDataset,
    LearningSource,
    OutcomeClass,
    RecommendationComplianceChecker,
    RecommendationEngine,
    SimulationComplianceChecker,
    SimulationContext,
    SimulationEngine,
    SimulationType,
    EvidenceRef,
)


def _sample(sid="s1", outcome=OutcomeClass.SUCCESS, attrs=()):
    return ExperienceSample(sample_id=sid, source=LearningSource.EXECUTION, outcome=outcome, attributes=attrs)


class TestLearning:
    def test_dataset_and_detector(self):
        dataset = LearningDataset()
        dataset.add(_sample(attrs=(("error", ""), ("domain", "policy"))))
        dataset.add(_sample(sid="s2", outcome=OutcomeClass.SUCCESS, attrs=(("error", ""), ("domain", "policy"))))
        assert dataset.size() == 2
        assert len(dataset.by_source(LearningSource.EXECUTION)) == 2
        assert LearningComplianceChecker().check()["certified"] is True
        assert LearningComplianceChecker().check(no_auto_apply=False)["certified"] is False


class TestEffectiveness:
    def test_report_and_analyzer(self):
        analyzer = EffectivenessAnalyzer()
        report = analyzer.analyze("policy", success_rate=0.9)
        assert report.overall_healthy is True
        low = analyzer.analyze("workflow", success_rate=0.4)
        assert low.overall_healthy is False


class TestSimulation:
    def test_simulate(self):
        engine = SimulationEngine()
        change = GovernanceChangeProposal("c1", "policy", "tighten controls")
        ctx = SimulationContext("scope", SimulationType.POLICY)
        result = engine.simulate(change, ctx)
        assert result.safe_to_propose is True
        risky = engine.simulate(change, ctx, acceptable_risk_delta=0.9)
        assert risky.safe_to_propose is False
        assert SimulationComplianceChecker().check()["certified"] is True


class TestImpact:
    def test_impact_analyze(self):
        analyzer = ImpactAnalyzer()
        assessment = analyzer.analyze(ImpactTarget.AGENT, "agent-1", severity=ImpactSeverity.LOW)
        assert assessment.acceptable is True
        high = analyzer.analyze(ImpactTarget.RUNTIME, "rt-1", severity=ImpactSeverity.HIGH)
        assert high.acceptable is False


class TestRecommendation:
    def test_recommendation(self):
        engine = RecommendationEngine()
        rec = engine.recommend("policy", "evaluate control", (EvidenceRef("e1", "execution"),), 0.9)
        assert rec.evidence_backed is True
        ctx = ApprovalContextBuilder().build(rec)
        assert ctx.requires_human_approval is True
        assert ctx.authority_retained is True
        assert RecommendationComplianceChecker().check()["certified"] is True
        assert RecommendationComplianceChecker().check(human_decides=False)["certified"] is False


class TestWorkspace:
    def test_workspace(self):
        dataset = LearningDataset()
        dataset.add(_sample())
        ws = GovernanceEvolutionWorkspace(dataset)
        assert len(ws.history_explorer()) == 1
        assert len(ws.approval_state()) == 0


class TestCertification:
    def test_full_certified(self):
        cert = AdaptiveGovernanceCertification()
        cert.learning_certification()
        cert.effectiveness_certification()
        cert.simulation_certification()
        cert.impact_certification()
        cert.recommendation_certification()
        cert.approval_boundary()
        cert.authority_boundary()
        cert.regression_verification()
        cert.production_readiness()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == AdaptiveCertStatus.CERTIFIED.value

    def test_not_certified(self):
        cert = AdaptiveGovernanceCertification()
        cert.authority_boundary(no_authority_change=False, no_auto_apply=False)
        cert.recommendation_certification(human_decides=False, recommend_only=False)
        assert cert.certify()["status"] == AdaptiveCertStatus.NOT_CERTIFIED.value
