"""Test IP-4.2-003 - Operational Prediction (MISSION-4.2).

Coverage: WP-21..WP-30 - consequence prediction, simulation, recommendation,
trust, risk, recommendation explainability, intelligence API, compliance,
end-to-end, baseline CI integration.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_intelligence.evidence_collection import (
    EvidenceModel,
    EvidenceSource,
)
from sam.operational_intelligence.root_cause_analysis import RootCauseAnalyzer
from sam.operational_intelligence.operational_diagnosis import (
    OperationalDiagnosisEngine,
)
from sam.operational_intelligence.consequence_prediction import (
    ConsequencePredictor,
)
from sam.operational_intelligence.operational_simulation import (
    OperationalSimulator,
)
from sam.operational_intelligence.recommendation_engine import (
    EvidenceBasedRecommendationEngine,
)
from sam.operational_intelligence.trust_assessment import TrustAssessor
from sam.operational_intelligence.risk_evaluation import RiskEvaluator, RiskFactor
from sam.operational_intelligence.recommendation_explainability import (
    RecommendationExplainer,
)
from sam.operational_intelligence.operational_intelligence_api import (
    OperationalIntelligenceAPI,
)
from sam.operational_intelligence.investigation_api import InvestigationAPI
from sam.operational_intelligence.diagnosis_api import DiagnosisAPI
from sam.operational_intelligence.intelligence_compliance import (
    IntelligenceComplianceChecker,
)


def _evidence(investigation_id, eid, source_id, category="health", **data):
    return EvidenceModel(
        evidence_id=eid,
        investigation_id=investigation_id,
        source=EvidenceSource(
            "provider" if source_id.startswith("provider") else "runtime",
            source_id,
        ),
        category=category,
        data=tuple(data.items()),
        metadata=(("k", "v"),),
        validated=True,
    )


def _make_diagnosis(evidence):
    analyzer = RootCauseAnalyzer()
    engine = OperationalDiagnosisEngine(analyzer)
    return engine, engine.diagnose("inv-1", "latency spike", evidence)


# ---------------------------------------------------------------------------
# WP-21 Consequence Prediction
# ---------------------------------------------------------------------------

class TestConsequencePrediction:
    def test_predict_consequences(self):
        def rules(action, evidences):
            return [
                ("Service restarts", 0.8, "low"),
                ("Temporary unavailability", 0.4, "medium"),
            ]

        predictor = ConsequencePredictor(rules)
        evidence = (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        result = predictor.predict("inv-1", "restart service", evidence)
        assert len(result.consequences) == 2
        assert result.riskiest is not None
        assert result.riskiest.likelihood == pytest.approx(0.8)

    def test_likelihood_clamped(self):
        def rules(action, evidences):
            return [("Outage", 5.0, "high")]

        predictor = ConsequencePredictor(rules)
        result = predictor.predict("inv-1", "act", ())
        assert result.consequences[0].likelihood == 1.0


# ---------------------------------------------------------------------------
# WP-22 Operational Simulation
# ---------------------------------------------------------------------------

class TestOperationalSimulation:
    def test_simulation_proposal(self):
        def model(scenario, evidences):
            return [
                ("success_rate", 0.97, "improved"),
                ("downtime_min", 2, "acceptable"),
            ]

        simulator = OperationalSimulator(model)
        proposal = simulator.simulate("inv-1", "scale providers", ())
        assert proposal.is_actionable
        assert len(proposal.outcomes) == 2

    def test_simulation_read_only(self):
        def model(scenario, evidences):
            return [("metric", 1, "note")]

        simulator = OperationalSimulator(model)
        proposal = simulator.simulate("inv-1", "x", ())
        assert proposal.investigation_id == "inv-1"


# ---------------------------------------------------------------------------
# WP-23 Recommendation Engine
# ---------------------------------------------------------------------------

class TestRecommendationEngine:
    def test_recommendation_evidence_based(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        evidence = (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        diag = engine.diagnose("inv-1", "x", evidence)
        rec_engine = EvidenceBasedRecommendationEngine()
        result = rec_engine.recommend(diag, evidence)
        assert result.recommendation_count == 1
        rec = result.recommendations[0]
        assert rec.evidence_ids == ("e1",)
        assert "provider" in rec.action.lower()

    def test_priority_by_confidence(self):
        engine = EvidenceBasedRecommendationEngine()
        assert engine._derive_priority(0.9) == "high"
        assert engine._derive_priority(0.6) == "medium"
        assert engine._derive_priority(0.2) == "low"


# ---------------------------------------------------------------------------
# WP-24 Trust Assessment
# ---------------------------------------------------------------------------

class TestTrustAssessment:
    def test_trust_score_calculation(self):
        _, diag = _make_diagnosis(
            (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        )
        assessor = TrustAssessor()
        trust = assessor.assess(
            "assess-1", diag.confidence, evidence_count=3
        )
        assert trust.trust_score > 0
        assert trust.level in ("low", "medium", "high")

    def test_trust_levels(self):
        assessor = TrustAssessor()
        from sam.operational_intelligence.operational_diagnosis import (
            DiagnosisConfidence,
        )

        low = assessor.assess(
            "a-1", DiagnosisConfidence(value=0.3), evidence_count=1
        )
        high = assessor.assess(
            "a-2", DiagnosisConfidence(value=1.0), evidence_count=20
        )
        assert low.level in ("low", "none")
        assert high.level == "high"


# ---------------------------------------------------------------------------
# WP-25 Risk Evaluation
# ---------------------------------------------------------------------------

class TestRiskEvaluation:
    def test_overall_risk(self):
        evaluator = RiskEvaluator()
        factors = (
            RiskFactor("outage", likelihood=0.8, impact="high"),
            RiskFactor("perf", likelihood=0.2, impact="low"),
        )
        risk = evaluator.evaluate("risk-1", factors)
        assert risk.overall_risk > 0
        assert risk.factors

    def test_no_factors_zero_risk(self):
        evaluator = RiskEvaluator()
        risk = evaluator.evaluate("risk-2", ())
        assert risk.overall_risk == 0.0
        assert risk.level == "none"


# ---------------------------------------------------------------------------
# WP-26 Recommendation Explainability
# ---------------------------------------------------------------------------

class TestRecommendationExplainability:
    def test_explanation_evidence_chain(self):
        engine = EvidenceBasedRecommendationEngine()
        evidence = (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        _, diag = _make_diagnosis(evidence)
        result = engine.recommend(diag, evidence)
        rec = result.recommendations[0]
        explainer = RecommendationExplainer()
        expl = explainer.explain(rec, evidence)
        assert expl.evidence_chain
        assert expl.evidence_chain[0][0] == "e1"


# ---------------------------------------------------------------------------
# WP-27 Operational Intelligence API
# ---------------------------------------------------------------------------

class TestOperationalIntelligenceAPI:
    def test_summary(self):
        api = OperationalIntelligenceAPI(
            investigations=InvestigationAPI(
                sessions=_S().sessions,
                evidences=_S().repo,
                investigations=_S().investigations,
                timelines={},
            ),
            diagnoses=DiagnosisAPI(engine=_S().engine),
            recommendations=(),
        )
        summary = api.summary()
        assert summary["generation_time"]
        assert "investigation_count" in summary


class _S:
    """Helper state ringan untuk test API."""

    def __init__(self):
        from sam.operational_intelligence.investigation_session import (
            InvestigationSessionManager,
        )
        from sam.operational_intelligence.investigation_model import (
            Investigation,
            InvestigationScope,
            InvestigationTarget,
            InvestigationMetadata,
        )
        from sam.operational_intelligence.evidence_collection import (
            EvidenceRepository,
        )
        from sam.operational_intelligence.root_cause_analysis import (
            RootCauseAnalyzer,
        )
        from sam.operational_intelligence.operational_diagnosis import (
            OperationalDiagnosisEngine,
        )

        self.sessions = InvestigationSessionManager()
        self.repo = EvidenceRepository()
        self.investigations = {}
        inv = Investigation.create(
            metadata=InvestigationMetadata(purpose="api test")
        )
        inv = inv.with_scope(
            InvestigationScope("s", (InvestigationTarget("runtime", "r1"),))
        )
        self.investigations[inv.investigation_id] = inv
        self.engine = OperationalDiagnosisEngine(RootCauseAnalyzer())


# ---------------------------------------------------------------------------
# WP-28 Intelligence Compliance
# ---------------------------------------------------------------------------

class TestIntelligenceCompliance:
    def test_certify_clean(self):
        checker = IntelligenceComplianceChecker()
        cert = checker.certify()
        assert cert["certified"] is True
        assert cert["violations"] == []

    def test_detects_execution(self):
        checker = IntelligenceComplianceChecker()
        cert = checker.certify(execution_called=True)
        assert not cert["certified"]
        assert any(v["kind"] == "execution" for v in cert["violations"])

    def test_detects_authority_leakage(self):
        checker = IntelligenceComplianceChecker()
        cert = checker.certify(authority_leakage=True)
        assert not cert["certified"]

    def test_forbidden_pattern(self):
        checker = IntelligenceComplianceChecker()
        assert not checker.check_source("def run():\n    gate.approve(\n    )").passed


# ---------------------------------------------------------------------------
# WP-29/30 End-to-End Certification + Baseline
# ---------------------------------------------------------------------------

class TestOperationalPredictionEndToEnd:
    def test_end_to_end_prediction(self):
        # Evidence -> Diagnosis -> Recommendation -> Consequence -> Trust
        evidence = (
            _evidence("inv-1", "e1", "provider-a", health="critical", cpu=98),
            _evidence("inv-1", "e2", "provider-a", health="degraded", cpu=82),
        )
        _, diag = _make_diagnosis(evidence)
        assert diag.confidence.value > 0

        rec_engine = EvidenceBasedRecommendationEngine()
        rec_result = rec_engine.recommend(diag, evidence)
        assert rec_result.recommendation_count == 1

        def rules(action, evidences):
            return [("Down", 0.3, "medium"), ("Restored", 0.9, "low")]

        predictor = ConsequencePredictor(rules)
        consequences = predictor.predict("inv-1", rec_result.recommendations[0].action, evidence)
        assert len(consequences.consequences) == 2

        explainer = RecommendationExplainer()
        expl = explainer.explain(
            rec_result.recommendations[0], evidence, consequences.consequences
        )
        assert expl.evidence_chain
        assert len(expl.predicted_consequences) == 2

        assessor = TrustAssessor()
        trust = assessor.assess("t-1", diag.confidence, evidence_count=2)
        assert trust.trust_score > 0

        # Compliance penuh
        checker = IntelligenceComplianceChecker()
        assert checker.certify()["certified"] is True
        assert checker.check_source("runtime.snapshot()").passed
