# -*- coding: utf-8 -*-
"""IP-3.6-B Platform Operations - Certification (WP-B1..B5, MISSION-3.6).

Menguji: Deployment Validation (WP-B1), Environment Validation (WP-B2),
Operational Configuration (WP-B3), Startup Verification (WP-B4),
Shutdown Verification (WP-B5), platform operations compliance (group PO).

Guardrail (MISSION-3.6): Platform Operations VERIFIES & REPORTS ops
readiness; TIDAK melakukan deploy/start/stop nyata. Seluruh pengamatan
diberikan sebagai input.
"""

import pytest

from sam.platform import (
    ConfigSetting,
    ConfigVerification,
    DeploymentArtifact,
    DeploymentValidation,
    EnvironmentFactor,
    EnvironmentValidation,
    ShutdownCheck,
    ShutdownVerification,
    StartupCheck,
    StartupVerification,
    platform_operations_compliance_check,
    validate_deployment,
    validate_environment,
    verify_configuration,
    verify_shutdown,
    verify_startup,
)


# --- WP-B1 Deployment Validation --------------------------------------------

def test_deployment_all_present():
    v = validate_deployment([
        DeploymentArtifact("app", present=True, version="3.6.0"),
        DeploymentArtifact("db", present=True, version="1"),
    ])
    assert v.ok
    assert v.present_ids == ("app", "db")


def test_deployment_missing_collected():
    v = validate_deployment([
        DeploymentArtifact("app", present=True),
        DeploymentArtifact("db", present=False),
    ])
    assert not v.ok
    assert v.missing_ids == ("db",)


# --- WP-B2 Environment Validation -------------------------------------------

def test_environment_all_satisfied():
    v = validate_environment([
        EnvironmentFactor("python", satisfied=True),
        EnvironmentFactor("network", satisfied=True),
    ])
    assert v.ok
    assert v.satisfied == ("python", "network")


def test_environment_unsatisfied_collected():
    v = validate_environment([
        EnvironmentFactor("python", satisfied=True),
        EnvironmentFactor("gpu", satisfied=False),
    ])
    assert not v.ok
    assert v.unsatisfied == ("gpu",)


# --- WP-B3 Operational Configuration ----------------------------------------

def test_config_all_aligned():
    v = verify_configuration([
        ConfigSetting("policy", "enforced", actual="enforced"),
        ConfigSetting("level", "info", actual="info"),
    ])
    assert v.ok
    assert v.aligned == ("policy", "level")


def test_config_misaligned_collected():
    v = verify_configuration([
        ConfigSetting("policy", "enforced", actual="off"),
        ConfigSetting("level", "info", actual="info"),
    ])
    assert not v.ok
    assert v.misaligned == ("policy",)


# --- WP-B4 Startup Verification ----------------------------------------------

def test_startup_all_passed():
    v = verify_startup([
        StartupCheck("boot", passed=True),
        StartupCheck("health", passed=True),
    ])
    assert v.ok
    assert v.passed_checks == ("boot", "health")


def test_startup_failed_collected():
    v = verify_startup([
        StartupCheck("boot", passed=True),
        StartupCheck("health", passed=False),
    ])
    assert not v.ok
    assert v.failed_checks == ("health",)


# --- WP-B5 Shutdown Verification ---------------------------------------------

def test_shutdown_all_completed():
    v = verify_shutdown([
        ShutdownCheck("flush", completed=True),
        ShutdownCheck("close", completed=True),
    ])
    assert v.ok
    assert v.completed == ("flush", "close")


def test_shutdown_incomplete_collected():
    v = verify_shutdown([
        ShutdownCheck("flush", completed=True),
        ShutdownCheck("close", completed=False),
    ])
    assert not v.ok
    assert v.incomplete == ("close",)


# --- PO compliance -----------------------------------------------------------

def test_platform_operations_compliance_passes():
    res = platform_operations_compliance_check()
    assert res.ok, res.messages
    assert res.group == "PO"
    assert res.forbidden_found == ()


# --- Exit criteria: verify ops, never execute ops ---------------------------

def test_po_has_no_execution_verbs():
    import sam.platform.platform_operations as po
    names = [n for n in dir(po) if not n.startswith("_")]
    forbidden = {"do_deploy", "start_service", "stop_service",
                 "kill_process", "write_config", "export_deployment"}
    assert not (forbidden & set(names))
