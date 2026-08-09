"""Test IP-4.6-003 - Production Platform (MISSION-4.6).

Coverage: WP-21..WP-30 - dashboard, trust visualization, history, experience
browser, metrics, certification, API, compliance, end-to-end, baseline.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.operational_workspace.production_platform import (
    DashboardRenderer,
    ExperienceBrowser,
    OperationalHistory,
    PlatformCertifier,
    PlatformMetricsCollector,
    TrustScore,
    TrustVisualizer,
)
from sam.operational_workspace.production_api import ProductionAPI
from sam.operational_workspace.production_compliance import (
    ProductionComplianceChecker,
)


# ---------------------------------------------------------------------------
# WP-21 Operational Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_snapshot(self):
        snap = DashboardRenderer.render(
            health="healthy", active_investigations=2, knowledge_entries=5
        )
        assert snap.health == "healthy"
        assert snap.active_investigations == 2


# ---------------------------------------------------------------------------
# WP-22 Trust Visualization
# ---------------------------------------------------------------------------

class TestTrustVisualization:
    def test_trust_score_high(self):
        trust = TrustVisualizer.compute(
            "execution", evidence_count=10, validation_rate=0.9
        )
        assert trust.level == "high"
        assert trust.score >= 0.8

    def test_trust_scores_from_evidence(self):
        trust = TrustVisualizer.compute(
            "learning", evidence_count=1, validation_rate=0.3
        )
        assert trust.level in ("low", "none")


# ---------------------------------------------------------------------------
# WP-23/24 Operational History + Experience Browser
# ---------------------------------------------------------------------------

class TestHistoryAndBrowser:
    def test_history_record_and_search(self):
        history = OperationalHistory()
        history.record("execution", "restarted service")
        history.record("investigation", "investigated cpu")
        assert history.count() == 2
        assert len(history.search("cpu")) == 1

    def test_experience_browser(self):
        history = OperationalHistory()
        history.record("execution", "restarted provider")
        browser = ExperienceBrowser(history)
        execs = browser.browse("execution")
        assert len(execs) == 1
        assert browser.trace(execs[0]["id"])["kind"] == "execution"


# ---------------------------------------------------------------------------
# WP-25/26 Operational Metrics + Certification
# ---------------------------------------------------------------------------

class TestMetricsAndCertification:
    def test_metrics_mean_trust(self):
        scores = (
            TrustScore("a", 0.8, 5),
            TrustScore("b", 0.6, 3),
        )
        metrics = PlatformMetricsCollector.collect(
            total_history=10, trust_scores=scores
        )
        assert metrics.mean_trust == 0.7
        assert metrics.total_history == 10

    def test_certification_all_pass(self):
        cert = PlatformCertifier.certify()
        assert cert.certified is True

    def test_certification_fails_on_foundation(self):
        cert = PlatformCertifier.certify(foundation_intact=False)
        assert cert.certified is False


# ---------------------------------------------------------------------------
# WP-27 Production API
# ---------------------------------------------------------------------------

class TestProductionAPI:
    def _build(self):
        history = OperationalHistory()
        history.record("execution", "restarted service")
        return ProductionAPI(history=history)

    def test_dashboard_via_api(self):
        api = self._build()
        assert api.dashboard(health="healthy")["health"] == "healthy"

    def test_trust_via_api(self):
        api = self._build()
        trust = api.trust("execution", evidence_count=8, validation_rate=0.9)
        assert trust["component"] == "execution"

    def test_history_via_api(self):
        api = self._build()
        assert len(api.history()) == 1

    def test_metrics_via_api(self):
        api = self._build()
        metrics = api.metrics(total_experiences=3, knowledge_count=2)
        assert metrics["total_history"] == 1


# ---------------------------------------------------------------------------
# WP-28 Production Compliance
# ---------------------------------------------------------------------------

class TestProductionCompliance:
    def test_certify_clean(self):
        checker = ProductionComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_no_execution_authority(self):
        checker = ProductionComplianceChecker()
        assert not checker.certify(no_execution_authority=False)["certified"]


# ---------------------------------------------------------------------------
# WP-29/30 End-to-End + Baseline
# ---------------------------------------------------------------------------

class TestProductionPlatformEndToEnd:
    def test_end_to_end_production(self):
        history = OperationalHistory()
        for i in range(3):
            history.record("execution", f"executed operation {i}")
        history.record("learning", "learned from feedback")

        api = ProductionAPI(history=history)

        # Dashboard
        dash = api.dashboard(health="degraded", completed_executions=3, knowledge_entries=4)
        assert dash["completed_executions"] == 3

        # Trust
        trust_execution = api.trust("execution", evidence_count=12, validation_rate=0.95)
        trust_learning = api.trust("learning", evidence_count=6, validation_rate=0.8)
        assert trust_execution["level"] == "high"

        # History browser
        assert api.trace(api.history("execution")[0]["id"]) is not None

        # Metrics dengan mean trust
        trust_obj = TrustScore(
            trust_execution["component"],
            trust_execution["score"],
            trust_execution["evidence_count"],
        )
        metrics = api.metrics(
            total_experiences=5, knowledge_count=4, trust_scores=(trust_obj,)
        )
        assert metrics["mean_trust"] > 0

        # Certification penuh (SAM 4.0 closing)
        cert = api.certify(
            foundation_intact=True, governance_preserved=True,
            all_capabilities_ready=True, baseline_ci_green=True,
        )
        assert cert["certified"] is True

        # Production compliance
        checker = ProductionComplianceChecker()
        assert checker.certify()["certified"] is True
