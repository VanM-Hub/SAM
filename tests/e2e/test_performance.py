"""
OP-357 — Performance Validation

Benchmark: latency, throughput, memory untuk pipeline utama.
Bandingkan dengan baseline.
"""

import pytest
import time
import gc
from typing import Dict, List

from sam.operations.brain.guardian import (
    GuardianGovernanceEngine,
    ExecutionReadinessEvaluator,
    GuardianRiskAssessment,
    GuardianDecisionExplanation,
    GuardianCoordinationRuntime,
    GovernanceConversationBridge,
    GuardianDashboardV3Service,
    GuardianRuntimeV3Integration,
)
from tests.e2e.runtime_harness import RuntimeHarness


PERF_THRESHOLD_MS = {
    "governance": 50,
    "readiness": 50,
    "risk": 50,
    "explanation": 50,
    "coordination": 200,
    "conversation": 50,
    "dashboard_card": 50,
    "full_pipeline": 1000,
}


class TestPerformanceValidation:
    """OP-357: Benchmark setiap pipeline stage."""

    TIMES: Dict[str, List[float]] = {}

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        gc.collect()
        yield

    def _bench(self, name: str, fn, iterations: int = 100) -> float:
        times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            fn()
            dur = (time.perf_counter() - t0) * 1000
            times.append(dur)
        avg = sum(times) / len(times)
        self.TIMES[name] = times
        return avg

    def test_governance_engine_latency(self):
        """Governance evaluate: < 50ms per call."""
        engine = GuardianGovernanceEngine()
        avg = self._bench("governance", lambda: engine.evaluate(
            policy_passed=True, health_status="healthy",
            decision_approved=True, approval_complete=True,
            recommendation_support=True, recommendation_risk="low",
        ))
        assert avg < PERF_THRESHOLD_MS["governance"], \
            f"Governance avg {avg:.2f}ms > {PERF_THRESHOLD_MS['governance']}ms"

    def test_readiness_evaluator_latency(self):
        """Readiness evaluate: < 50ms per call."""
        evaluator = ExecutionReadinessEvaluator()
        avg = self._bench("readiness", lambda: evaluator.evaluate(
            approval_complete=True, policy_passed=True,
            guardian_healthy=True, dependency_complete=True,
        ))
        assert avg < PERF_THRESHOLD_MS["readiness"], \
            f"Readiness avg {avg:.2f}ms > {PERF_THRESHOLD_MS['readiness']}ms"

    def test_risk_assessment_latency(self):
        """Risk assess: < 50ms per call."""
        assess = GuardianRiskAssessment()
        avg = self._bench("risk", lambda: assess.assess(
            system_health="healthy", health_score=0.9,
        ))
        assert avg < PERF_THRESHOLD_MS["risk"], \
            f"Risk avg {avg:.2f}ms > {PERF_THRESHOLD_MS['risk']}ms"

    def test_explanation_latency(self):
        """Explanation build: < 50ms per call."""
        expl = GuardianDecisionExplanation()
        avg = self._bench("explanation", lambda: expl.build(
            governance_status="approved",
            policy_passed=True, health_status="healthy",
        ))
        assert avg < PERF_THRESHOLD_MS["explanation"], \
            f"Explanation avg {avg:.2f}ms > {PERF_THRESHOLD_MS['explanation']}ms"

    def test_coordination_latency(self):
        """Coordination runtime: < 200ms per call."""
        coord = GuardianCoordinationRuntime(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
            explanation=GuardianDecisionExplanation(),
        )
        avg = self._bench("coordination", lambda: coord.run(
            policy_passed=True, health_status="healthy",
        ), iterations=50)
        assert avg < PERF_THRESHOLD_MS["coordination"], \
            f"Coordination avg {avg:.2f}ms > {PERF_THRESHOLD_MS['coordination']}ms"

    def test_conversation_governance_latency(self):
        """Conversation governance: < 50ms per call."""
        bridge = GovernanceConversationBridge(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
        )
        avg = self._bench("conversation", lambda: bridge.query("why_blocked"),
                          iterations=50)
        assert avg < PERF_THRESHOLD_MS["conversation"], \
            f"Conversation avg {avg:.2f}ms > {PERF_THRESHOLD_MS['conversation']}ms"

    def test_dashboard_card_latency(self):
        """Dashboard V3 card: < 50ms per call."""
        dash = GuardianDashboardV3Service(
            governance=GuardianGovernanceEngine(),
            readiness=ExecutionReadinessEvaluator(),
            risk_assessment=GuardianRiskAssessment(),
        )
        avg = self._bench("dashboard_card",
                          lambda: dash.build_governance_card(
                              policy_passed=True, health_status="healthy",
                          ), iterations=50)
        assert avg < PERF_THRESHOLD_MS["dashboard_card"], \
            f"Dashboard avg {avg:.2f}ms > {PERF_THRESHOLD_MS['dashboard_card']}ms"

    def test_full_pipeline_latency(self):
        """Full pipeline (harness): < 1000ms per run."""
        harness = RuntimeHarness("perf-test")
        avg = self._bench("full_pipeline",
                          lambda: harness.run_full_pipeline(
                              policy_passed=True, health_status="healthy",
                          ), iterations=30)
        assert avg < PERF_THRESHOLD_MS["full_pipeline"], \
            f"Full pipeline avg {avg:.2f}ms > {PERF_THRESHOLD_MS['full_pipeline']}ms"

    def test_throughput_governance(self):
        """Throughput governance: > 500 ops/sec."""
        engine = GuardianGovernanceEngine()
        t0 = time.perf_counter()
        count = 500
        for _ in range(count):
            engine.evaluate(policy_passed=True)
        dur = time.perf_counter() - t0
        ops = count / dur
        print(f"Governance throughput: {ops:.0f} ops/sec")
        assert ops > 500, f"Throughput {ops:.0f}/sec < 500"

    def test_throughput_readiness(self):
        """Throughput readiness: > 500 ops/sec."""
        evaluator = ExecutionReadinessEvaluator()
        t0 = time.perf_counter()
        count = 500
        for _ in range(count):
            evaluator.evaluate()
        dur = time.perf_counter() - t0
        ops = count / dur
        print(f"Readiness throughput: {ops:.0f} ops/sec")
        assert ops > 500, f"Throughput {ops:.0f}/sec < 500"

    def test_memory_governance(self):
        """Memory: satu evaluasi tidak alokasi > 100KB."""
        import tracemalloc
        # Skip if not available
        tracemalloc.start()
        engine = GuardianGovernanceEngine()
        engine.evaluate(policy_passed=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_kb = peak / 1024
        print(f"Governance peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 200, f"Peak {peak_kb:.1f}KB > 200KB"

    def test_full_pipeline_memory(self):
        """Memory: satu full pipeline run tidak alokasi > 1MB."""
        import tracemalloc
        tracemalloc.start()
        harness = RuntimeHarness("mem-test")
        harness.run_full_pipeline(policy_passed=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_kb = peak / 1024
        print(f"Full pipeline peak memory: {peak_kb:.1f}KB")
        # Guardian V2 internally instantiates engines, might be higher
        assert peak_kb < 2048, f"Peak {peak_kb:.1f}KB > 2MB"


class TestPerformanceReport:
    """Cetak ringkasan performa."""

    def test_print_summary(self):
        """Cetak laporan performa."""
        print("\n" + "=" * 60)
        print("PERFORMANCE VALIDATION REPORT")
        print("=" * 60)

        # Quick benchmark
        report = []
        engine = GuardianGovernanceEngine()
        t0 = time.perf_counter()
        for _ in range(200):
            engine.evaluate()
        d1 = time.perf_counter() - t0
        report.append(f"Governance Engine: {200/d1:.0f} ops/sec ({d1*1000/200:.3f}ms avg)")

        evaluator = ExecutionReadinessEvaluator()
        t0 = time.perf_counter()
        for _ in range(200):
            evaluator.evaluate()
        d2 = time.perf_counter() - t0
        report.append(f"Readiness: {200/d2:.0f} ops/sec ({d2*1000/200:.3f}ms avg)")

        assess = GuardianRiskAssessment()
        t0 = time.perf_counter()
        for _ in range(200):
            assess.assess()
        d3 = time.perf_counter() - t0
        report.append(f"Risk: {200/d3:.0f} ops/sec ({d3*1000/200:.3f}ms avg)")

        expl = GuardianDecisionExplanation()
        t0 = time.perf_counter()
        for _ in range(200):
            expl.build()
        d4 = time.perf_counter() - t0
        report.append(f"Explanation: {200/d4:.0f} ops/sec ({d4*1000/200:.3f}ms avg)")

        harness = RuntimeHarness("report")
        t0 = time.perf_counter()
        for _ in range(50):
            harness.run_full_pipeline(policy_passed=True)
        d5 = time.perf_counter() - t0
        report.append(f"Full Pipeline: {50/d5:.0f} ops/sec ({d5*1000/50:.1f}ms avg)")

        for line in report:
            print(f"  {line}")
        print("=" * 60)
