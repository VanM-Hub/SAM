# -*- coding: utf-8 -*-
"""IP-3.6-A Production Governance - Certification (WP-A1..A5, MISSION-3.6).

Menguji: Production Governance Profile (WP-A1), Operational Policy Validation
(WP-A2), Governance Readiness (WP-A3), Operational Compliance (WP-A4),
Governance Baseline Verification (WP-A5), production governance compliance
(group PG).

Guardrail (MISSION-3.6): Production Governance MEASURES & REPORTS readiness;
ia TIDAK mengeksekusi/menerapkan governance. Seluruh input diberikan dari luar.
"""

import pytest

from sam.platform import (
    BaselineEntry,
    BaselineVerification,
    ComplianceCheckItem,
    GovernanceProfile,
    GovernanceProfileStatus,
    GovernanceReadiness,
    PolicyEntry,
    PolicyValidationResult,
    ReadinessInput,
    assess_governance_profile,
    assess_readiness,
    operational_compliance_score,
    production_governance_compliance_check,
    validate_operational_policies,
    verify_governance_baseline,
)


# --- WP-A1 Production Governance Profile ------------------------------------

def test_default_profile_labels():
    p = GovernanceProfile()
    assert p.governance_areas == ("decision", "policy", "audit", "accountability")
    assert p.label_set == ("decision", "policy", "audit", "accountability")


def test_profile_assess_ok_when_covered():
    st = assess_governance_profile(
        GovernanceProfile(),
        covered_areas=["decision", "policy", "audit", "accountability"],
        states=["ready", "degraded"])
    assert st.profile_ok
    assert "decision" in st.areas_covered
    assert st.states_observed == ("degraded", "ready")


def test_profile_assess_fails_when_area_missing():
    st = assess_governance_profile(
        GovernanceProfile(), covered_areas=["policy"], states=["ready"])
    assert not st.profile_ok


def test_profile_status_immutable():
    st = GovernanceProfileStatus(areas_covered=("a",), states_observed=("x",))
    with pytest.raises(Exception):
        st.areas_covered = ("b",)  # frozen dataclass


# --- WP-A2 Operational Policy Validation ------------------------------------

def test_policy_validation_all_valid():
    res = validate_operational_policies([
        PolicyEntry("p1", "policy one", enforced=True),
        PolicyEntry("p2", "policy two", enforced=True),
    ])
    assert res.all_valid
    assert res.valid_count == 2


def test_policy_validation_invalid_collected():
    res = validate_operational_policies([
        PolicyEntry("p1", "ok", enforced=True),
        PolicyEntry("p2", "not enforced", enforced=False),
        PolicyEntry("", "empty id", enforced=True),
    ])
    assert not res.all_valid
    assert "p2" in res.invalid_ids
    assert "" in res.invalid_ids


# --- WP-A3 Governance Readiness ----------------------------------------------

def test_readiness_overall():
    r = assess_readiness(ReadinessInput(0.8, 0.6, 0.7))
    assert r.overall == pytest.approx(0.7)
    assert r.ready  # >= 0.7


def test_readiness_not_ready_low():
    r = assess_readiness(ReadinessInput(0.3, 0.4, 0.5))
    assert not r.ready
    assert r.overall == pytest.approx(0.4)


def test_readiness_clamps_values():
    r = assess_readiness(ReadinessInput(1.5, -0.2, 0.9))
    # clamp ke [0,1]
    assert r.governance == 1.0
    assert r.policy == 0.0
    assert r.evidence == 0.9


# --- WP-A4 Operational Compliance --------------------------------------------

def test_compliance_score():
    passed, total, ratio = operational_compliance_score([
        ComplianceCheckItem("c1", passed=True),
        ComplianceCheckItem("c2", passed=True),
        ComplianceCheckItem("c3", passed=False),
    ])
    assert (passed, total) == (2, 3)
    assert ratio == pytest.approx(0.6667)


def test_compliance_score_empty():
    passed, total, ratio = operational_compliance_score([])
    assert (passed, total, ratio) == (0, 0, 1.0)


# --- WP-A5 Governance Baseline Verification ----------------------------------

def test_baseline_matches():
    v = verify_governance_baseline([
        BaselineEntry("policy", "enforced", actual="enforced"),
        BaselineEntry("audit", "on", actual="on"),
    ])
    assert v.ok
    assert v.matched == ("policy", "audit")


def test_baseline_mismatch_collected():
    v = verify_governance_baseline([
        BaselineEntry("policy", "enforced", actual="revoked"),
        BaselineEntry("audit", "on", actual="on"),
    ])
    assert not v.ok
    assert v.mismatched == ("policy",)
    assert v.matched == ("audit",)


# --- PG compliance -----------------------------------------------------------

def test_production_governance_compliance_passes():
    res = production_governance_compliance_check()
    assert res.ok, res.messages
    assert res.group == "PG"
    assert res.forbidden_found == ()


# --- Exit criteria: measure & report, never enforce -------------------------

def test_pg_has_no_enforcement_verbs():
    import sam.platform.production_governance as pg
    names = [n for n in dir(pg) if not n.startswith("_")]
    forbidden = {"enforce_policy", "apply_policy", "deploy", "rollback",
                 "grant_access", "promote_to_prod"}
    assert not (forbidden & set(names))
