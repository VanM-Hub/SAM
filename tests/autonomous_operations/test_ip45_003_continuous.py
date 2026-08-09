"""Test IP-4.5-003 - Continuous Autonomous Operations (MISSION-4.5).

Coverage: WP-21..WP-30 - continuous verification, optimization, health
monitoring, autonomous recommendation, readiness, metrics, API, compliance,
end-to-end.
"""
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.autonomous_operations.continuous_operations import (
    AutonomousMetricsCollector,
    AutonomousRecommender,
    ContinuousVerifier,
    HealthMonitor,
    OperationalHealth,
    ReadinessVerifier,
)
from sam.autonomous_operations.autonomous_operations_api import (
    AutonomousOperationsAPI,
)
from sam.autonomous_operations.continuous_compliance import (
    ContinuousComplianceChecker,
)


# ---------------------------------------------------------------------------
# WP-21 Continuous Verification
# ---------------------------------------------------------------------------

class TestContinuousVerification:
    def test_verify_all_ok(self):
        verifier = ContinuousVerifier()
        result = verifier.verify()
        assert result.passed is True

    def test_verify_detects_issue(self):
        verifier = ContinuousVerifier()
        result = verifier.verify(provider_ok=False)
        assert result.passed is False

    def test_history_accumulates(self):
        verifier = ContinuousVerifier()
        verifier.verify()
        verifier.verify()
        assert len(verifier.history()) == 2


# ---------------------------------------------------------------------------
# WP-22/23 Health Monitoring
# ---------------------------------------------------------------------------

class TestHealthMonitor:
    def test_healthy(self):
        health = HealthMonitor.assess(runtime_health="healthy", provider_health="healthy")
        assert health.overall == "healthy"

    def test_critical_overrides(self):
        health = HealthMonitor.assess(runtime_health="critical", provider_health="healthy")
        assert health.overall == "critical"

    def test_degraded(self):
        health = HealthMonitor.assess(runtime_health="healthy", provider_health="degraded")
        assert health.overall == "degraded"


# ---------------------------------------------------------------------------
# WP-24 Autonomous Recommendation
# ---------------------------------------------------------------------------

class TestAutonomousRecommender:
    def test_critical_escalates(self):
        health = OperationalHealth(overall="critical", runtime_health="critical")
        rec = AutonomousRecommender.recommend(health=health)
        assert rec.priority == "high"
        assert "approval" in rec.action.lower()

    def test_healthy_monitor(self):
        health = OperationalHealth(overall="healthy")
        rec = AutonomousRecommender.recommend(health=health)
        assert rec.priority == "low"
        assert "monitor" in rec.action.lower()

    def test_recommendation_evidence(self):
        health = OperationalHealth(overall="degraded")
        rec = AutonomousRecommender.recommend(health=health, evidence_ids=("e1",))
        assert rec.evidence_ids == ("e1",)


# ---------------------------------------------------------------------------
# WP-25/26 Readiness + Metrics
# ---------------------------------------------------------------------------

class TestReadinessAndMetrics:
    def test_readiness_all(self):
        readiness = ReadinessVerifier.verify()
        assert readiness.ready is True

    def test_readiness_not_ready(self):
        readiness = ReadinessVerifier.verify(provider_ready=False)
        assert readiness.ready is False
        assert readiness.dimensions["provider"] is False

    def test_metrics_collect(self):
        metrics = AutonomousMetricsCollector.collect(
            verifications=3, recommendations=2, health_status="degraded", readiness=True
        )
        assert metrics.verifications == 3
        assert metrics.readiness is True


# ---------------------------------------------------------------------------
# WP-27 Autonomous Operations API
# ---------------------------------------------------------------------------

class TestAutonomousOperationsAPI:
    def test_verify_via_api(self):
        api = AutonomousOperationsAPI(verifier=ContinuousVerifier())
        assert api.verify()["passed"] is True

    def test_health_via_api(self):
        api = AutonomousOperationsAPI(verifier=ContinuousVerifier())
        health = api.health(runtime_health="healthy", provider_health="degraded")
        assert health["overall"] == "degraded"

    def test_summary_via_api(self):
        api = AutonomousOperationsAPI(verifier=ContinuousVerifier())
        summary = api.summary(runtime_health="healthy", provider_health="healthy")
        assert summary["health"]["overall"] == "healthy"
        assert summary["readiness"]["ready"] is True
        assert summary["metrics"]["verifications"] == 0  # verifier baru (belum verify)


# ---------------------------------------------------------------------------
# WP-28 Continuous Compliance
# ---------------------------------------------------------------------------

class TestContinuousCompliance:
    def test_certify_clean(self):
        checker = ContinuousComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_recommendation_only(self):
        checker = ContinuousComplianceChecker()
        assert not checker.certify(recommendation_only=False)["certified"]

    def test_requires_approval(self):
        checker = ContinuousComplianceChecker()
        assert not checker.certify(approval_before_execution=False)["certified"]

    def test_authority_leakage(self):
        checker = ContinuousComplianceChecker()
        assert not checker.certify(authority_leakage=True)["certified"]


# ---------------------------------------------------------------------------
# WP-29/30 End-to-End + Baseline
# ---------------------------------------------------------------------------

class TestContinuousOperationsEndToEnd:
    def test_end_to_end_continuous(self):
        verifier = ContinuousVerifier()
        api = AutonomousOperationsAPI(verifier=verifier)

        # Verifikasi berkelanjutan
        v1 = api.verify()
        v2 = api.verify(provider_ok=True, knowledge_ok=True)
        assert v2["passed"] is True

        # Kesehatan menurun -> rekomendasi naikkan prioritas
        health = api.health(runtime_health="critical", provider_health="healthy")
        obj = HealthMonitor.assess(runtime_health="critical", provider_health="healthy")
        rec = api.recommend(obj, evidence_ids=("e1",))
        assert rec["priority"] == "high"

        # Readiness & summary
        readiness = api.readiness(runtime_ready=True, provider_ready=True, governance_ready=True, knowledge_ready=True)
        assert readiness["ready"] is True
        summary = api.summary(runtime_health="healthy", provider_health="healthy")
        assert summary["metrics"]["verifications"] == 2

        # Compliance
        checker = ContinuousComplianceChecker()
        assert checker.certify()["certified"] is True
        assert not checker.certify(recommendation_only=False)["certified"]
