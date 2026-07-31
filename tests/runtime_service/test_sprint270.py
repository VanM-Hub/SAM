"""Sprint 270 - Certification (7 dimensi).

Program D - Runtime Services & Deployment.
Configuration, Security, Lifecycle, Plugin, Determinism,
Immutability, ProductionReadiness.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.certifier import RuntimeCertifier, DimensionResult
from sam.runtime_service.certification_report import (
    CertificationReport, build_certification_report,
)


def test_dimensions_present():
    for d in ("Configuration", "Security", "Lifecycle", "Plugin",
              "Determinism", "Immutability", "ProductionReadiness"):
        assert d in RuntimeCertifier.DIMENSIONS


def test_initial_not_certified():
    c = RuntimeCertifier()
    assert c.passed() == 0
    assert c.is_certified() is False
    assert c.summary()["total"] == 7


def test_check_one_dimension():
    c = RuntimeCertifier()
    c.check("Configuration", True, "ok")
    assert c.passed() == 1
    assert c.is_certified() is False


def test_check_unknown_dimension():
    c = RuntimeCertifier()
    with pytest.raises(ValueError):
        c.check("Bogus", True)


def test_full_certification():
    c = RuntimeCertifier()
    for d in c.DIMENSIONS:
        c.check(d, True)
    assert c.is_certified() is True
    assert c.passed() == 7


def test_partial_certification():
    c = RuntimeCertifier()
    for d in c.DIMENSIONS:
        c.check(d, True)
    c.check("Security", False, "secret hardcoded")
    assert c.is_certified() is False
    assert c.passed() == 6


def test_results_list():
    c = RuntimeCertifier()
    c.check("Configuration", True)
    results = c.results()
    assert isinstance(results[0], DimensionResult)
    assert results[0].passed is True


def test_dimension_result_immutable():
    r = DimensionResult(dimension="Security", passed=True, detail="ok")
    with pytest.raises(Exception):
        r.passed = False


def test_summary_dict():
    c = RuntimeCertifier()
    s = c.summary()
    assert s["passed"] == 0
    assert s["certified"] is False
    assert len(s["dimensions"]) == 7


def test_report_not_certified():
    c = RuntimeCertifier()
    rep = build_certification_report(c)
    assert rep.certified is False
    assert rep.passed == 0
    assert rep.total == 7


def test_report_certified():
    c = RuntimeCertifier()
    for d in c.DIMENSIONS:
        c.check(d, True)
    rep = build_certification_report(c)
    assert rep.certified is True
    assert rep.passed == 7


def test_report_as_dict():
    c = RuntimeCertifier()
    c.check("Configuration", True, "detail-x")
    rep = build_certification_report(c)
    ad = rep.as_dict()
    assert ad["version"] == "27.0.0"
    assert len(ad["dimensions"]) == 7
    cfg = [x for x in ad["dimensions"] if x["dimension"] == "Configuration"][0]
    assert cfg["detail"] == "detail-x"


def test_report_immutable():
    rep = CertificationReport(certified=True, passed=7)
    with pytest.raises(Exception):
        rep.passed = 0


def test_certifier_all_seven_distinct():
    c = RuntimeCertifier()
    assert len(set(c.DIMENSIONS)) == 7
