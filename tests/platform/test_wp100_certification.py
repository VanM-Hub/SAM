# -*- coding: utf-8 -*-
"""IP-3.6-E Mission Certification - Certification (WP-E1..E5, MISSION-3.6).

Menguji: End-to-End Production Certification (WP-E1), Mission Readiness
Assessment (WP-E2), Operational Regression (WP-E3), Compliance Regression
(WP-E4), Mission Engineering Report (WP-E5), mission certification
compliance (MC).

Guardrail (MISSION-3.6): Mission Certification ASSESSES & REPORTS; TIDAK
memberikan otoritas/status operational.
"""

import pytest

from sam.platform import (
    ComplianceGroup,
    ComplianceRegression,
    MissionEngineeringReport,
    MissionReadiness,
    OperationalRegression,
    ProductionCertification,
    ReadinessGate,
    RegressionSuite,
    ReportSection,
    TrackResult,
    assess_mission_readiness,
    build_engineering_report,
    certify_end_to_end,
    mission_certification_compliance_check,
    run_compliance_regression,
    run_operational_regression,
)


# --- WP-E1 End-to-End Production Certification -------------------------------

def test_certification_all_tracks_ok():
    c = certify_end_to_end([
        TrackResult("A", ok=True), TrackResult("B", ok=True),
        TrackResult("C", ok=True), TrackResult("D", ok=True),
    ])
    assert c.ok
    assert c.ratio == 1.0
    assert c.failed_tracks == ()


def test_certification_failed_track():
    c = certify_end_to_end([
        TrackResult("A", ok=True), TrackResult("B", ok=False),
    ])
    assert not c.ok
    assert c.failed_tracks == ("B",)
    assert c.ratio == pytest.approx(0.5)


# --- WP-E2 Mission Readiness Assessment --------------------------------------

def test_readiness_ready_all_met():
    r = assess_mission_readiness([
        ReadinessGate("g1", met=True), ReadinessGate("g2", met=True),
    ])
    assert r.ready
    assert r.score == 1.0


def test_readiness_unmet_collected():
    r = assess_mission_readiness([
        ReadinessGate("g1", met=True), ReadinessGate("g2", met=False),
    ])
    assert not r.ready
    assert r.unmet_gates == ("g2",)
    assert r.score == pytest.approx(0.5)


# --- WP-E3 Operational Regression --------------------------------------------

def test_operational_regression_all_pass():
    r = run_operational_regression([
        RegressionSuite("platform", passed=True, count=129),
        RegressionSuite("citizen", passed=True, count=157),
    ])
    assert r.ok
    assert r.total_cases == 286


def test_operational_regression_failed_suite():
    r = run_operational_regression([
        RegressionSuite("platform", passed=True, count=129),
        RegressionSuite("gov", passed=False, count=122),
    ])
    assert not r.ok
    assert r.failed_suites == ("gov",)
    assert r.total_cases == 251


# --- WP-E4 Compliance Regression ---------------------------------------------

def test_compliance_regression_all_pass():
    r = run_compliance_regression([
        ComplianceGroup("PEX", passed=True), ComplianceGroup("MEX", passed=True),
        ComplianceGroup("CX", passed=True), ComplianceGroup("EX", passed=True),
        ComplianceGroup("PG", passed=True), ComplianceGroup("PO", passed=True),
        ComplianceGroup("OE", passed=True), ComplianceGroup("PR", passed=True),
        ComplianceGroup("MC", passed=True),
    ])
    assert r.ok
    assert r.failed_groups == ()


def test_compliance_regression_failed_group():
    r = run_compliance_regression([
        ComplianceGroup("PEX", passed=True), ComplianceGroup("PG", passed=False),
    ])
    assert not r.ok
    assert r.failed_groups == ("PG",)


# --- WP-E5 Mission Engineering Report ----------------------------------------

def test_report_build_and_all_verified():
    rep = build_engineering_report([
        ReportSection("Track A", verified=True),
        ReportSection("Track B", verified=True),
    ], "recommendation text")
    assert isinstance(rep, MissionEngineeringReport)
    assert rep.all_verified
    assert rep.section_titles() == ("Track A", "Track B")
    assert rep.recommendation == "recommendation text"


def test_report_not_all_verified():
    rep = build_engineering_report([
        ReportSection("Track A", verified=True),
        ReportSection("Track B", verified=False),
    ], "hold")
    assert not rep.all_verified


# --- MC compliance -----------------------------------------------------------

def test_mission_certification_compliance_passes():
    res = mission_certification_compliance_check()
    assert res.ok, res.messages
    assert res.group == "MC"
    assert res.forbidden_found == ()


# --- Exit criteria: assessment & report, never grant authority --------------

def test_mc_has_no_authority_verbs():
    import sam.platform.mission_certification as mc
    names = [n for n in dir(mc) if not n.startswith("_")]
    forbidden = {"declare_operational", "grant_operational", "approve_mission",
                 "grant_authority", "adjudicate", "command_deploy"}
    assert not (forbidden & set(names))
