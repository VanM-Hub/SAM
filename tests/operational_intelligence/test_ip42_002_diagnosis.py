"""Test IP-4.2-002 - Operational Diagnosis (MISSION-4.2).

Coverage: WP-11..WP-20 - root cause, failure correlation, dependency,
impact, diagnosis, confidence, API, explainability, compliance, e2e.
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
from sam.operational_intelligence.failure_correlation import FailureCorrelator
from sam.operational_intelligence.dependency_analysis import DependencyAnalyzer
from sam.operational_intelligence.impact_assessment import ImpactAssessor
from sam.operational_intelligence.operational_diagnosis import (
    OperationalDiagnosisEngine,
)
from sam.operational_intelligence.diagnosis_api import (
    DiagnosisAPI,
    DiagnosisNotFoundError,
)
from sam.operational_intelligence.diagnosis_compliance import (
    DiagnosisComplianceChecker,
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


# ---------------------------------------------------------------------------
# WP-11 Root Cause Analysis
# ---------------------------------------------------------------------------

class TestRootCauseAnalysis:
    def test_identifies_abnormal_source(self):
        analyzer = RootCauseAnalyzer()
        evidence = (
            _evidence("inv-1", "e1", "provider-a", health="critical", cpu=95),
            _evidence("inv-1", "e2", "runtime-core", health="healthy", cpu=40),
        )
        result = analyzer.analyze("inv-1", "high latency", evidence)
        assert result.overall_confidence > 0
        assert result.top_finding is not None
        assert result.top_finding.supporting_evidence == ("e1",)

    def test_no_abnormal_no_finding(self):
        analyzer = RootCauseAnalyzer()
        evidence = (
            _evidence("inv-1", "e1", "runtime-core", health="healthy", cpu=30),
        )
        result = analyzer.analyze("inv-1", "normal", evidence)
        assert result.overall_confidence == 0.0
        assert result.top_finding is None

    def test_every_finding_backed_by_evidence(self):
        analyzer = RootCauseAnalyzer()
        evidence = (
            _evidence("inv-1", "e1", "provider-a", health="critical"),
            _evidence("inv-1", "e2", "provider-a", health="degraded"),
        )
        result = analyzer.analyze("inv-1", "x", evidence)
        assert result.findings
        assert all(f.supporting_evidence for f in result.findings)


# ---------------------------------------------------------------------------
# WP-12 Failure Correlation
# ---------------------------------------------------------------------------

class TestFailureCorrelation:
    def test_correlates_same_source(self):
        correlator = FailureCorrelator()
        failures = (
            _evidence("inv-1", "e1", "provider-a", health="critical"),
            _evidence("inv-1", "e2", "provider-a", health="critical"),
        )
        result = correlator.correlate("inv-1", failures)
        assert len(result.correlations) == 1
        assert result.correlations[0].evidence_count == 2

    def test_no_correlation_single(self):
        correlator = FailureCorrelator()
        single = (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        result = correlator.correlate("inv-1", single)
        assert len(result.correlations) == 0


# ---------------------------------------------------------------------------
# WP-13 Dependency Analysis
# ---------------------------------------------------------------------------

class TestDependencyAnalysis:
    def test_builds_graph(self):
        analyzer = DependencyAnalyzer()
        result = analyzer.analyze(
            "inv-1",
            components={
                "runtime": ("provider",),
                "provider": ("network",),
                "network": (),
            },
        )
        assert len(result.nodes) == 3
        assert result.component("runtime").dependencies == ("provider",)
        assert result.component("provider").dependents == ("runtime",)

    def test_critical_components(self):
        analyzer = DependencyAnalyzer()
        result = analyzer.analyze(
            "inv-1",
            components={
                "core": ("db",),
                "api": ("core",),
                "web": ("core",),
                "db": (),
            },
        )
        # 'core' punya 2 dependents (api, web) -> kritis
        assert "core" in result.critical_components


# ---------------------------------------------------------------------------
# WP-14 Impact Assessment
# ---------------------------------------------------------------------------

class TestImpactAssessment:
    def test_direct_and_indirect_impact(self):
        analyzer = DependencyAnalyzer()
        dependency = analyzer.analyze(
            "inv-1",
            components={
                "db": (),
                "core": ("db",),
                "api": ("core",),
                "web": ("api",),
            },
        )
        assessor = ImpactAssessor()
        impact = assessor.assess("inv-1", "db", dependency)
        assert impact.impact_count == 3
        levels = {i.impact_level for i in impact.impacted}
        assert "direct" in levels
        assert "indirect" in levels


# ---------------------------------------------------------------------------
# WP-15/16 Operational Diagnosis + Confidence
# ---------------------------------------------------------------------------

class TestOperationalDiagnosis:
    def test_diagnosis_with_confidence(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        evidence = (
            _evidence("inv-1", "e1", "provider-a", health="critical"),
            _evidence("inv-1", "e2", "runtime-core", health="healthy"),
        )
        diag = engine.diagnose("inv-1", "latency spike", evidence)
        assert diag.root_cause
        assert diag.confidence.value > 0
        assert diag.evidence_ids == ("e1",)
        assert diag.confidence.level in ("low", "medium", "high")

    def test_confidence_calculator_levels(self):
        from sam.operational_intelligence.operational_diagnosis import (
            DiagnosisConfidenceCalculator as Calc,
        )

        analyzer = RootCauseAnalyzer()
        result = analyzer.analyze("inv-1", "x", ())
        conf = Calc.calculate(result)
        assert conf.level == "none"
        assert conf.value == 0.0


# ---------------------------------------------------------------------------
# WP-17 Diagnosis API
# ---------------------------------------------------------------------------

class TestDiagnosisAPI:
    def test_register_and_get(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        api = DiagnosisAPI(engine=engine)
        evidence = (
            _evidence("inv-1", "e1", "provider-a", health="critical"),
        )
        diag = engine.diagnose("inv-1", "x", evidence)
        api.register_diagnosis(diag)
        assert api.get_diagnosis(diag.diagnosis_id)["root_cause"]

    def test_not_found_raises(self):
        api = DiagnosisAPI(engine=OperationalDiagnosisEngine(RootCauseAnalyzer()))
        with pytest.raises(DiagnosisNotFoundError):
            api.get_diagnosis("nonexistent")

    def test_list_by_investigation(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        api = DiagnosisAPI(engine=engine)
        d1 = engine.diagnose("inv-1", "a", (_evidence("inv-1", "e1", "p", health="critical"),))
        d2 = engine.diagnose("inv-2", "b", (_evidence("inv-2", "e2", "p", health="critical"),))
        api.register_diagnosis(d1)
        api.register_diagnosis(d2)
        assert len(api.list_diagnoses("inv-1")) == 1


# ---------------------------------------------------------------------------
# WP-18 Diagnosis Explainability
# ---------------------------------------------------------------------------

class TestDiagnosisExplainability:
    def test_explanation_has_evidence_chain(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        api = DiagnosisAPI(engine=engine)
        evidence = (_evidence("inv-1", "e1", "provider-a", health="critical"),)
        diag = engine.diagnose("inv-1", "x", evidence)
        api.register_diagnosis(diag)
        expl = api.explain_diagnosis(diag.diagnosis_id, evidence)
        assert expl["explanation"]
        assert len(expl["evidence_chain"]) == 1
        assert expl["evidence_chain"][0][0] == "e1"


# ---------------------------------------------------------------------------
# WP-19 Diagnosis Compliance
# ---------------------------------------------------------------------------

class TestDiagnosisCompliance:
    def test_evidence_based_default(self):
        checker = DiagnosisComplianceChecker()
        result = checker.check_evidence_based()
        assert result.passed

    def test_detects_execution(self):
        checker = DiagnosisComplianceChecker()
        result = checker.check_evidence_based(has_execution=True)
        assert not result.passed

    def test_detects_no_evidence(self):
        checker = DiagnosisComplianceChecker()
        result = checker.check_evidence_based(has_evidence=False)
        assert not result.passed

    def test_forbidden_pattern(self):
        checker = DiagnosisComplianceChecker()
        assert not checker.check_source("provider.execute()").passed

    def test_certify(self):
        checker = DiagnosisComplianceChecker()
        assert checker.certify()["certified"] is True


# ---------------------------------------------------------------------------
# WP-20 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestDiagnosisEndToEnd:
    def test_end_to_end_diagnosis(self):
        analyzer = RootCauseAnalyzer()
        engine = OperationalDiagnosisEngine(analyzer)
        evidences = (
            _evidence("inv-1", "e1", "provider-a", health="critical", cpu=97),
            _evidence("inv-1", "e2", "provider-a", health="degraded", cpu=80),
            _evidence("inv-1", "e3", "runtime-core", health="healthy"),
        )
        diag = engine.diagnose("inv-1", "high cpu & latency", evidences)
        assert diag.confidence.value > 0
        assert "provider" in diag.root_cause.lower()

        api = DiagnosisAPI(engine=engine)
        api.register_diagnosis(diag)
        assert len(api.list_diagnoses("inv-1")) == 1
        expl = api.explain_diagnosis(diag.diagnosis_id, evidences)
        assert expl["evidence_chain"]

        checker = DiagnosisComplianceChecker()
        assert checker.certify()["certified"] is True
        assert checker.check_source("runtime.snapshot()").passed
