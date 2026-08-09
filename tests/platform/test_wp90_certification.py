# -*- coding: utf-8 -*-
"""IP-3.6-D Production Reliability - Certification (WP-D1..D5, MISSION-3.6).

Menguji: Reliability Verification (WP-D1), Recoverability Validation (WP-D2),
Operational Stability (WP-D3), Production Diagnostics (WP-D4),
Long-running Verification (WP-D5), production reliability compliance (PR).

Guardrail (MISSION-3.6): Production Reliability VERIFIES & DIAGNOSES dari
input pengamatan; TIDAK menjalankan recovery/failover/intervensi.
"""

import pytest

from sam.platform import (
    DiagnosticFinding,
    DiagnosticsSummary,
    LongRunningObservation,
    LongRunningVerification,
    RecoveryPlanPiece,
    RecoverabilityValidation,
    ReliabilityObservation,
    ReliabilityVerification,
    StabilityAssessment,
    StabilitySample,
    assess_stability,
    production_reliability_compliance_check,
    summarize_diagnostics,
    validate_recoverability,
    verify_long_running,
    verify_reliability,
)


# --- WP-D1 Reliability Verification -----------------------------------------

def test_reliability_ok_above_threshold():
    v = verify_reliability([
        ReliabilityObservation("api", attempts=10, successes=10),
        ReliabilityObservation("db", attempts=10, successes=9),
    ], threshold=0.9)
    assert v.ok  # 1.0 & 0.9 >= 0.9
    assert v.reliable == ("api", "db")


def test_reliability_degraded_below_threshold():
    v = verify_reliability([
        ReliabilityObservation("api", attempts=10, successes=10),
        ReliabilityObservation("db", attempts=10, successes=5),
    ], threshold=0.9)
    assert not v.ok
    assert v.degraded == ("db",)


def test_reliability_zero_success_rate_when_no_attempts():
    o = ReliabilityObservation("idle", attempts=0, successes=0)
    assert o.success_rate == 0.0


# --- WP-D2 Recoverability Validation -----------------------------------------

def test_recoverability_all_available():
    v = validate_recoverability([
        RecoveryPlanPiece("restore", available=True),
        RecoveryPlanPiece("rollback", available=True),
    ])
    assert v.ok
    assert v.available == ("restore", "rollback")


def test_recoverability_unavailable_collected():
    v = validate_recoverability([
        RecoveryPlanPiece("restore", available=True),
        RecoveryPlanPiece("rollback", available=False),
    ])
    assert not v.ok
    assert v.unavailable == ("rollback",)


# --- WP-D3 Operational Stability ---------------------------------------------

def test_stability_all_stable():
    a = assess_stability([
        StabilitySample("d1", stable=True),
        StabilitySample("d2", stable=True),
    ])
    assert a.ok
    assert a.stable_periods == ("d1", "d2")


def test_stability_unstable_collected():
    a = assess_stability([
        StabilitySample("d1", stable=True),
        StabilitySample("d2", stable=False),
    ])
    assert not a.ok
    assert a.unstable_periods == ("d2",)


# --- WP-D4 Production Diagnostics --------------------------------------------

def test_diagnostics_groups_severity():
    s = summarize_diagnostics([
        DiagnosticFinding("f1", "critical"),
        DiagnosticFinding("f2", "warning"),
        DiagnosticFinding("f3", "info"),
        DiagnosticFinding("f4", "warning"),
    ])
    assert s.has_critical
    assert s.critical == ("f1",)
    assert s.warnings == ("f2", "f4")
    assert s.info_findings == ("f3",)


def test_diagnostics_no_critical():
    s = summarize_diagnostics([
        DiagnosticFinding("f1", "info"),
        DiagnosticFinding("f2", "warning"),
    ])
    assert not s.has_critical
    assert s.critical == ()


# --- WP-D5 Long-running Verification -----------------------------------------

def test_long_running_ok():
    v = verify_long_running([
        LongRunningObservation("s1", 168.0, ok=True),
        LongRunningObservation("s2", 72.0, ok=True),
    ])
    assert v.ok
    assert v.sessions_ok == 2
    assert v.sessions_degraded == 0
    assert v.total_duration_hours == pytest.approx(240.0)


def test_long_running_degraded():
    v = verify_long_running([
        LongRunningObservation("s1", 168.0, ok=True),
        LongRunningObservation("s2", 12.0, ok=False),
    ])
    assert not v.ok
    assert (v.sessions_ok, v.sessions_degraded) == (1, 1)


# --- PR compliance -----------------------------------------------------------

def test_production_reliability_compliance_passes():
    res = production_reliability_compliance_check()
    assert res.ok, res.messages
    assert res.group == "PR"
    assert res.forbidden_found == ()


# --- Exit criteria: verify & diagnose, never fix ----------------------------

def test_pr_has_no_intervention_verbs():
    import sam.platform.production_reliability as pr
    names = [n for n in dir(pr) if not n.startswith("_")]
    forbidden = {"run_recovery", "trigger_failover", "self_heal",
                 "restart_component", "patch_runtime", "kill_task"}
    assert not (forbidden & set(names))
