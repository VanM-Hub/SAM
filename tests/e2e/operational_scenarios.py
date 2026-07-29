"""
OP-352 — Operational Scenarios (50+)

Setiap skenario menghasilkan output deterministik.
Verifikasi berdasarkan SEMANTIC OUTPUT (governance_passed, readiness_passed, risk_safe),
bukan pipeline crash-free.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from tests.e2e.runtime_harness import RuntimeHarness, PipelineRun, StageResult


def make_scenario(
    scenario: str,
    harness: RuntimeHarness,
    expected_governance_passed: Optional[bool] = None,
    expected_readiness_passed: Optional[bool] = None,
    expected_risk_safe: Optional[bool] = None,
    expected_pipeline_ok: bool = True,
    expected_evidence_min: int = 1,
    **kw: Any,
) -> tuple:
    """Jalankan skenario dengan harness. Return (scenario_name, PipelineRun, expected_values)."""
    run = harness.run_full_pipeline(**kw)
    return (
        scenario,
        run,
        expected_governance_passed,
        expected_readiness_passed,
        expected_risk_safe,
        expected_pipeline_ok,
        expected_evidence_min,
    )


def verify(scenario_name: str, run: PipelineRun,
           exp_gov: Optional[bool], exp_ready: Optional[bool],
           exp_risk: Optional[bool], exp_pipe: bool, exp_ev: int) -> Tuple[bool, str]:
    errors: List[str] = []

    # Pipeline integrity: all stages must run without crash
    if run.all_passed != exp_pipe:
        # trace which stage(s) crashed
        crashed = [s.stage for s in run.stages if not s.success]
        errors.append(f"pipeline_ok expected={exp_pipe} got={run.all_passed} crashed={crashed}")

    # Evidence minimum
    if run.total_evidence < exp_ev:
        errors.append(f"evidence expected>={exp_ev} got={run.total_evidence}")

    # Semantic: governance passed?
    if exp_gov is not None and run.governance_passed != exp_gov:
        errors.append(f"governance_passed expected={exp_gov} got={run.governance_passed}")

    # Semantic: readiness passed?
    if exp_ready is not None and run.readiness_passed != exp_ready:
        errors.append(f"readiness_passed expected={exp_ready} got={run.readiness_passed}")

    # Semantic: risk safe?
    if exp_risk is not None and run.risk_safe != exp_risk:
        errors.append(f"risk_safe expected={exp_risk} got={run.risk_safe}")

    passed = len(errors) == 0
    return (passed, "; ".join(errors) if errors else "OK")


def all_scenarios() -> List[tuple]:
    """Hasilkan 50+ skenario operasional."""
    scenarios: List[tuple] = []
    harness = RuntimeHarness("op-352-50-scenarios")

    # ── 1. Normal / Happy Path ──────────────────────────
    scenarios.append(make_scenario(
        "normal-01-happy_path", harness,
        expected_governance_passed=True,
        expected_readiness_passed=True,
        expected_risk_safe=True,
        guardian_healthy=True,
        policy_passed=True, policy_violations=0,
        health_status="healthy", health_score=0.95,
        decision_approved=True, decision_confidence=0.9,
        approval_complete=True, approval_required=2, approval_granted=2,
        recommendation_support=True, recommendation_risk="low",
        conflict_detected=False, dependency_complete=True,
        confidence_score=0.9, evidence_count=5,
    ))
    scenarios.append(make_scenario(
        "normal-02-all_green", harness,
        expected_governance_passed=True,
        expected_readiness_passed=True,
        expected_risk_safe=True,
        guardian_healthy=True, guardian_score=1.0,
        policy_passed=True, policy_violations=0,
        health_status="healthy", health_score=1.0,
        decision_approved=True, decision_confidence=1.0,
        approval_complete=True, approval_required=1, approval_granted=1,
        recommendation_support=True, recommendation_risk="low",
        conflict_detected=False, dependency_complete=True,
        confidence_score=1.0, evidence_count=10,
    ))

    # ── 2. Policy ───────────────────────────────────────
    scenarios.append(make_scenario(
        "policy-01-violations_2", harness,
        expected_governance_passed=False,
        policy_passed=False, policy_violations=2,
        health_status="healthy", health_score=0.8,
    ))
    scenarios.append(make_scenario(
        "policy-02-violations_critical", harness,
        expected_governance_passed=False,
        policy_passed=False, policy_violations=10,
        health_status="healthy", health_score=0.8,
    ))
    scenarios.append(make_scenario(
        "policy-03_no_violations", harness,
        expected_governance_passed=True,
        policy_passed=True, policy_violations=0,
        health_status="healthy", health_score=0.8,
    ))

    # ── 3. Health ───────────────────────────────────────
    scenarios.append(make_scenario(
        "health-01_degraded", harness,
        expected_governance_passed=True,
        health_status="degraded", health_score=0.6,
    ))
    scenarios.append(make_scenario(
        "health-02_critical", harness,
        expected_governance_passed=False,
        health_status="critical", health_score=0.2,
    ))
    scenarios.append(make_scenario(
        "health-03_borderline_ok", harness,
        expected_governance_passed=True,
        health_status="healthy", health_score=0.51,
    ))
    scenarios.append(make_scenario(
        "health-04_edge_critical", harness,
        expected_governance_passed=False,
        health_status="critical", health_score=0.49,
    ))

    # ── 4. Approval ─────────────────────────────────────
    scenarios.append(make_scenario(
        "approval-01_backlog", harness,
        expected_governance_passed=False,
        health_status="healthy",
        approval_complete=False, approval_required=10, approval_granted=2,
    ))
    scenarios.append(make_scenario(
        "approval-02_fully_approved", harness,
        expected_governance_passed=True,
        health_status="healthy",
        approval_complete=True, approval_required=5, approval_granted=5,
    ))
    scenarios.append(make_scenario(
        "approval-03_none_granted", harness,
        expected_governance_passed=False,
        health_status="healthy",
        approval_complete=False, approval_required=3, approval_granted=0,
    ))
    scenarios.append(make_scenario(
        "approval-04_excess_approvals", harness,
        expected_governance_passed=True,
        health_status="healthy",
        approval_complete=True, approval_required=2, approval_granted=5,
    ))

    # ── 5. Decision ─────────────────────────────────────
    scenarios.append(make_scenario(
        "decision-01_low_confidence", harness,
        expected_governance_passed=False,
        health_status="healthy",
        decision_approved=False, decision_confidence=0.3,
        approval_complete=True,
    ))
    scenarios.append(make_scenario(
        "decision-02_approved_edge", harness,
        expected_governance_passed=True,
        health_status="healthy",
        decision_approved=True, decision_confidence=0.71,
        approval_complete=True,
    ))
    scenarios.append(make_scenario(
        "decision-03_rejected", harness,
        expected_governance_passed=False,
        health_status="healthy",
        decision_approved=False, decision_confidence=0.1,
        approval_complete=True,
    ))

    # ── 6. Recommendation ───────────────────────────────
    scenarios.append(make_scenario(
        "recommendation-01_high_risk", harness,
        expected_governance_passed=False,
        health_status="healthy",
        recommendation_support=False, recommendation_risk="high",
    ))
    scenarios.append(make_scenario(
        "recommendation-02_medium_risk", harness,
        expected_governance_passed=False,  # medium risk → deferred
        health_status="healthy",
        recommendation_support=True, recommendation_risk="medium",
    ))
    scenarios.append(make_scenario(
        "recommendation-03_low_risk", harness,
        expected_governance_passed=True,
        health_status="healthy",
        recommendation_support=True, recommendation_risk="low",
    ))

    # ── 7. Readiness ────────────────────────────────────
    scenarios.append(make_scenario(
        "readiness-01_approval_blocked", harness,
        expected_readiness_passed=False,
        health_status="healthy",
        approval_complete=False, approval_rate=0.0,
    ))
    scenarios.append(make_scenario(
        "readiness-02_guardian_unhealthy", harness,
        expected_readiness_passed=False,
        guardian_healthy=False, guardian_score=0.2,
    ))
    scenarios.append(make_scenario(
        "readiness-03_conflict", harness,
        expected_readiness_passed=False,  # conflict → blocked
        health_status="healthy", approval_complete=True,
        conflict_detected=True, conflict_count=2,
    ))
    scenarios.append(make_scenario(
        "readiness-04_dependency_pending", harness,
        expected_readiness_passed=False,
        health_status="healthy", approval_complete=True,
        dependency_complete=False, dependency_pending=3,
    ))
    scenarios.append(make_scenario(
        "readiness-05_low_confidence", harness,
        expected_readiness_passed=False,  # low confidence → REVIEW (not ready)
        health_status="healthy", approval_complete=True,
        confidence_score=0.4, confidence_threshold=0.7,
    ))

    # ── 8. Risk ─────────────────────────────────────────
    scenarios.append(make_scenario(
        "risk-01_critical_health", harness,
        expected_risk_safe=False,
        system_health="critical", health_score=0.1,
    ))
    scenarios.append(make_scenario(
        "risk-02_high_complexity", harness,
        expected_risk_safe=False,  # critical complexity → unsafe
        execution_complexity="critical",
    ))
    scenarios.append(make_scenario(
        "risk-03_dependency_all_pending", harness,
        expected_risk_safe=True,
        dependency_pending=0, dependency_count=0,
    ))
    scenarios.append(make_scenario(
        "risk-04_all_high", harness,
        expected_risk_safe=False,
        system_health="critical", health_score=0.1,
        policy_violations=5,
        execution_complexity="critical",
        dependency_pending=10, dependency_count=10,
        approval_missing=5, approval_required=5,
        confidence_score=0.1, evidence_quality=0.1,
    ))

    # ── 9. Combined ─────────────────────────────────────
    scenarios.append(make_scenario(
        "combined-01_repeated_failure", harness,
        expected_governance_passed=False,
        execution_failures=5,
        policy_passed=False, policy_violations=3,
        health_status="degraded", health_score=0.5,
    ))
    scenarios.append(make_scenario(
        "combined-02_evidence_insufficient", harness,
        expected_governance_passed=True,
        evidence_count=0, evidence_minimum=3,
        confidence_score=0.3, confidence_threshold=0.6,
    ))
    scenarios.append(make_scenario(
        "combined-03_approval_rate_low", harness,
        expected_governance_passed=False,
        approval_complete=False, approval_rate=0.2,
    ))
    scenarios.append(make_scenario(
        "combined-04_all_healthy", harness,
        expected_governance_passed=True,
        expected_readiness_passed=True,
        expected_risk_safe=True,
        policy_passed=True, policy_violations=0,
        health_status="healthy", health_score=0.9,
        decision_approved=True, decision_confidence=0.9,
        approval_complete=True, approval_required=2, approval_granted=2,
        recommendation_support=True, recommendation_risk="low",
        guardian_healthy=True, guardian_score=1.0,
        confidence_score=0.9, evidence_count=5,
        conflict_detected=False, dependency_complete=True,
    ))

    # ── 10. Edge Cases ──────────────────────────────────
    scenarios.append(make_scenario(
        "edge-01_unknown_health", harness,
        expected_governance_passed=False,
        health_status="unknown", health_score=0.0,
    ))
    scenarios.append(make_scenario(
        "edge-02_all_bad", harness,
        expected_governance_passed=False,
        health_score=0.0, decision_confidence=0.0,
        approval_granted=0, approval_required=1,
        guardian_score=0.0, recommendation_risk="high",
        policy_passed=False, policy_violations=5,
    ))
    scenarios.append(make_scenario(
        "edge-03_all_good", harness,
        expected_governance_passed=True,
        expected_readiness_passed=True,
        expected_risk_safe=True,
        health_score=1.0, decision_confidence=1.0,
        approval_granted=10, approval_required=10,
        guardian_score=1.0, recommendation_risk="low",
        policy_passed=True, policy_violations=0,
        health_status="healthy",
        approval_complete=True,
        conflict_detected=False, dependency_complete=True,
        confidence_score=1.0, evidence_count=10,
    ))
    scenarios.append(make_scenario(
        "edge-04_no_approval_needed", harness,
        expected_governance_passed=True,
        health_status="healthy",
        approval_complete=True, approval_required=0, approval_granted=0,
    ))
    scenarios.append(make_scenario(
        "edge-05_guardian_disconnected", harness,
        expected_readiness_passed=False,
        guardian_healthy=False, guardian_score=0.0,
    ))

    # ── 11. Provider ────────────────────────────────────
    scenarios.append(make_scenario(
        "provider-01_offline", harness,
        expected_governance_passed=False,
        health_status="critical", health_score=0.1,
        policy_violations=3,
    ))
    scenarios.append(make_scenario(
        "provider-02_throttled", harness,
        expected_governance_passed=False,
        health_status="degraded", health_score=0.4,
        decision_confidence=0.5,
    ))

    # ── 12. Scheduler ───────────────────────────────────
    scenarios.append(make_scenario(
        "scheduler-01_overload", harness,
        expected_governance_passed=True,  # overload tidak langsung block governance
        execution_failures=3,
    ))
    scenarios.append(make_scenario(
        "scheduler-02_queue_full", harness,
        expected_governance_passed=True,
    ))

    # ── 13. Mission ─────────────────────────────────────
    scenarios.append(make_scenario(
        "mission-01_dependency_failed", harness,
        expected_readiness_passed=False,
        dependency_complete=False, dependency_pending=5,
    ))
    scenarios.append(make_scenario(
        "mission-02_conflict_parallel", harness,
        expected_readiness_passed=False,  # conflict → blocked
        conflict_detected=True, conflict_count=3,
    ))

    # ── 14. Trust ───────────────────────────────────────
    scenarios.append(make_scenario(
        "trust-01_low", harness,
        expected_governance_passed=True,
        confidence_score=0.3, confidence_threshold=0.8,
    ))
    scenarios.append(make_scenario(
        "trust-02_recovering", harness,
        expected_governance_passed=True,
        confidence_score=0.65, confidence_threshold=0.7,
    ))

    # ── 15. Failure Injection ───────────────────────────
    scenarios.append(make_scenario(
        "failure-01_health_degradation", harness,
        expected_governance_passed=True,
        health_status="degraded", health_score=0.55,
    ))
    scenarios.append(make_scenario(
        "failure-02_repeated_crash", harness,
        expected_governance_passed=False,
        execution_failures=5,
        policy_passed=False, policy_violations=3,
        health_status="critical",
    ))

    # ── 16. Recovery ────────────────────────────────────
    scenarios.append(make_scenario(
        "recovery-01_after_failure", harness,
        expected_governance_passed=True,
        health_status="healthy", health_score=0.8,
        policy_passed=True, policy_violations=0,
        decision_approved=True, decision_confidence=0.9,
        approval_complete=True,
    ))

    # ── 17. Replay ──────────────────────────────────────
    scenarios.append(make_scenario(
        "replay-01_mismatch", harness,
        expected_governance_passed=True,
        policy_passed=True,
    ))

    # ── 18. Workspace ───────────────────────────────────
    scenarios.append(make_scenario(
        "workspace-01_locked", harness,
        expected_governance_passed=True,
    ))

    # ── 19. Audit ───────────────────────────────────────
    scenarios.append(make_scenario(
        "audit-01_growth", harness,
        expected_governance_passed=True,
        health_status="healthy",
        decision_approved=True, decision_confidence=0.85,
    ))

    # ── 20. Mixed Edge ──────────────────────────────────
    scenarios.append(make_scenario(
        "mixed-01_health_degraded_approval_ok", harness,
        expected_governance_passed=True,
        health_status="degraded", health_score=0.51,
        policy_passed=True, policy_violations=0,
        decision_approved=True, decision_confidence=0.7,
        approval_complete=True, approval_required=1, approval_granted=1,
    ))
    scenarios.append(make_scenario(
        "mixed-02_policy_fail_but_rest_ok", harness,
        expected_governance_passed=False,
        health_status="healthy", health_score=0.9,
        policy_passed=False, policy_violations=1,
        decision_approved=True, decision_confidence=0.9,
        approval_complete=True,
    ))
    scenarios.append(make_scenario(
        "mixed-03_critical_health_policy_ok", harness,
        expected_governance_passed=False,
        health_status="critical", health_score=0.15,
        policy_passed=True, policy_violations=0,
        decision_approved=True, decision_confidence=0.8,
        approval_complete=True,
    ))

    # ── 21. Stress / Random (8 extra → total 50+) ──────
    # 8 stress scenarios dengan parameter eksplisit agar mudah diverifikasi
    stress_data = [
        # (i, gov_pass, ready_pass, risk_safe, params...)
        (1, True,  True,  True,  dict(policy_passed=True, policy_violations=0, health_status='healthy', health_score=0.9, decision_approved=True, decision_confidence=0.9, approval_complete=True, approval_required=2, approval_granted=2, guardian_healthy=True, confidence_score=0.8, evidence_count=3, conflict_detected=False, dependency_complete=True)),
        (2, False, False, True,  dict(policy_passed=True, policy_violations=0, health_status='healthy', health_score=0.9, decision_approved=False, decision_confidence=0.5, approval_complete=False, approval_required=2, approval_granted=1, guardian_healthy=True, confidence_score=0.8, evidence_count=3, conflict_detected=False, dependency_complete=True)),
        (3, False, False, True,  dict(policy_passed=True, policy_violations=0, health_status='healthy', health_score=0.9, decision_approved=True, decision_confidence=0.9, approval_complete=False, approval_required=2, approval_granted=0, guardian_healthy=True, confidence_score=0.8, evidence_count=3, conflict_detected=False, dependency_complete=True)),
        (4, True,  True,  True,  dict(policy_passed=True, policy_violations=0, health_status='healthy', health_score=0.9, decision_approved=True, decision_confidence=0.9, approval_complete=True, approval_required=2, approval_granted=3, guardian_healthy=True, confidence_score=0.8, evidence_count=3, conflict_detected=False, dependency_complete=True)),
        (5, False, True,  False, dict(policy_passed=True, policy_violations=0, health_status='critical', health_score=0.1, decision_approved=False, decision_confidence=0.3, approval_complete=True, approval_required=2, approval_granted=2, guardian_healthy=True, confidence_score=0.8, evidence_count=3, conflict_detected=False, dependency_complete=True, system_health='critical')),
        (6, False, False, False, dict(policy_passed=True, policy_violations=0, health_status='critical', health_score=0.2, decision_approved=True, decision_confidence=0.9, approval_complete=True, approval_required=2, approval_granted=2, guardian_healthy=False, guardian_score=0.2, confidence_score=0.3, evidence_count=0, conflict_detected=False, dependency_complete=True)),
        (7, False, False, False, dict(policy_passed=False, policy_violations=2, health_status='critical', health_score=0.2, decision_approved=False, decision_confidence=0.3, approval_complete=False, approval_required=2, approval_granted=1, guardian_healthy=False, guardian_score=0.2, confidence_score=0.3, evidence_count=0, conflict_detected=True, dependency_complete=False, dependency_pending=3)),
        (8, True,  False, False, dict(policy_passed=True, policy_violations=0, health_status='degraded', health_score=0.55, decision_approved=True, decision_confidence=0.9, approval_complete=True, approval_required=2, approval_granted=2, guardian_healthy=False, guardian_score=0.3, confidence_score=0.8, evidence_count=5, conflict_detected=True, dependency_complete=True)),
    ]
    for idx, gov_pass, ready_pass, risk_safe, params in stress_data:
        scenarios.append(make_scenario(
            f"stress-{idx:02d}", harness,
            expected_governance_passed=gov_pass,
            expected_readiness_passed=ready_pass,
            expected_risk_safe=risk_safe,
            **params,
        ))

    return scenarios


def run_all(verbose: bool = False) -> tuple:
    """Jalankan semua skenario. Return (passed, total, errors)."""
    scenarios = all_scenarios()
    passed = 0
    errors: List[str] = []

    for s in scenarios:
        scenario_name, run, exp_gov, exp_ready, exp_risk, exp_pipe, exp_ev = s
        ok, msg = verify(scenario_name, run, exp_gov, exp_ready, exp_risk, exp_pipe, exp_ev)
        if ok:
            passed += 1
            if verbose:
                print(f"  \u2705 {scenario_name}")
        else:
            errors.append(f"{scenario_name}: {msg}")
            if verbose:
                print(f"  \u274c {scenario_name}: {msg}")

    return passed, len(scenarios), errors
