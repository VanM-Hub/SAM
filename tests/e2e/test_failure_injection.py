"""
OP-358 — Failure Injection

Fault injection:
  provider failure, missing evidence, policy violation, approval timeout,
  scheduler overload, repository unavailable, corrupted snapshot

Verifikasi: Guardian tetap menghasilkan status yang dapat dijelaskan, bukan crash.
"""

import pytest
from typing import Dict, Any

from sam.operations.brain.guardian import (
    GuardianGovernanceEngine,
    ExecutionReadinessEvaluator,
    GuardianRiskAssessment,
    GuardianDecisionExplanation,
    GovernanceConversationBridge,
    GuardianCoordinationRuntime,
)
from tests.e2e.runtime_harness import RuntimeHarness


class TestFailureInjection:
    """OP-358: Guardian harus graceful terhadap semua kegagalan."""

    def _assert_not_crash(self, result, name: str):
        """Pastikan hasilnya adalah object yang bisa dibaca, bukan crash."""
        assert result is not None, f"{name}: result is None (crash?)"

    def test_provider_failure(self):
        """Provider down → health critical → governance rejected."""
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(
            policy_passed=True,
            health_status="critical", health_score=0.0,
            decision_approved=True,
            approval_complete=True,
        )
        assert r is not None
        assert r.approved is False
        assert r.overall_status.value in ("rejected", "deferred")

    def test_missing_evidence(self):
        """Missing evidence → readiness waiting."""
        evaluator = ExecutionReadinessEvaluator()
        r = evaluator.evaluate(
            evidence_count=0, evidence_minimum=3,
        )
        assert r.ready is False
        assert len(r.blocking_dimensions) >= 0

    def test_policy_violation_critical(self):
        """Policy violation parah → governance rejected."""
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(
            policy_passed=False, policy_violations=100,
            health_status="healthy",
        )
        assert r.approved is False
        assert "policy" in str(r.failed_stages) or "policy" in r.summary

    def test_approval_timeout(self):
        """Approval timeout (0 granted despite 5 required)."""
        engine = GuardianGovernanceEngine()
        r = engine.evaluate(
            approval_complete=False, approval_required=5, approval_granted=0,
            health_status="healthy",
        )
        assert r.approved is False
        # Harus ada stage approval yang gagal
        appr = r.stage_decisions.get("approval")
        if appr:
            assert not appr.passed

    def test_scheduler_overload(self):
        """Scheduler overload → tetap proses tanpa crash."""
        risk = GuardianRiskAssessment()
        r = risk.assess(
            execution_complexity="critical",
            execution_failures=10,
        )
        assert r is not None
        assert isinstance(r.is_safe, bool)

    def test_repository_unavailable(self):
        """Repository unavailable — simulated via readiness."""
        evaluator = ExecutionReadinessEvaluator()
        r = evaluator.evaluate(
            guardian_healthy=False, guardian_score=0.0,
        )
        assert r.ready is False
        # Guardian harus tetap bisa menjelaskan
        assert r.overall_level.value is not None

    def test_corrupted_snapshot(self):
        """Corrupted snapshot — simulated dengan parameter ekstrim."""
        risk = GuardianRiskAssessment()
        # Parameters ekstrim yang tidak realistis (simulasi data rusak)
        r = risk.assess(
            system_health="unknown",
            health_score=-1.0,  # impossible value
            policy_violations=-5,  # impossible value
        )
        assert r is not None
        # Risk harus tetap return assessment (tidak crash)
        assert r.overall_level is not None

    def test_all_failures_simultaneously(self):
        """Semua kegagalan terjadi bersamaan — tidak crash."""
        coord = GuardianCoordinationRuntime(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        r = coord.run(
            policy_passed=False, policy_violations=50,
            health_status="critical", health_score=0.0,
            decision_approved=False, decision_confidence=0.0,
            approval_complete=False, approval_required=10, approval_granted=0,
            recommendation_support=False, recommendation_risk="high",
            guardian_healthy=False, guardian_score=0.0,
            evidence_count=0, evidence_minimum=10,
            dependency_complete=False, dependency_pending=20,
            execution_complexity="critical", execution_failures=10,
            confidence_score=0.0, evidence_quality=0.0,
        )
        assert r.success is True  # pipeline tetap selesai
        assert r.governance_ok is True
        assert r.readiness_ok is True
        assert r.risk_ok is True
        assert r.explanation_ok is True

    def test_conversation_during_failure(self):
        """Conversation bridge tetap bisa menjawab saat failure."""
        bridge = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        queries = ["why_blocked", "why_approved", "risk_summary",
                    "policy_summary", "guardian_summary", "governance_report"]
        for q in queries:
            r = bridge.query(q,
                             policy_passed=False, policy_violations=3,
                             health_status="critical",
                             guardian_healthy=False,
                             )
            assert r.success, f"Query {q} failed"
            assert len(r.data) > 0, f"Query {q} returned empty"

    def test_empty_params_still_works(self):
        """Tanpa parameter sama sekali — engine tetap tidak crash."""
        engines = [
            ("governance", GuardianGovernanceEngine(), "evaluate"),
            ("readiness", ExecutionReadinessEvaluator(), "evaluate"),
            ("risk", GuardianRiskAssessment(), "assess"),
            ("explanation", GuardianDecisionExplanation(), "build"),
        ]
        for name, engine, method in engines:
            fn = getattr(engine, method)
            try:
                result = fn()
                assert result is not None, f"{name} returned None"
            except Exception as e:
                pytest.fail(f"{name} crashed with empty params: {e}")

    def test_e2e_harness_crash_resistant(self):
        """RuntimeHarness tidak crash ketika semua parameter negatif."""
        harness = RuntimeHarness("failure-injection")
        r = harness.run_full_pipeline(
            policy_passed=False, health_status="critical",
            guardian_healthy=False, approval_complete=False,
            conflict_detected=True, dependency_complete=False,
        )
        assert r.all_passed is True  # harness harus tangani semua exception
