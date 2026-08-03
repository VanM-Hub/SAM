"""L3 behavioral checker tests (P1-008 Batch 4)."""

import pytest

from sam.compliance.checks.concrete.builder import (
    _L3_DETERMINISM, _L3_IDEMPOTENCY, _L3_LIFECYCLE, _L3_ISOLATION,
)
from sam.compliance.checks.concrete import behavioral as _beh


def _l3_ids():
    ids = ["L3-IS03", "L3-IS04", "L3-IS01", "L3-IS02"]
    ids += ["L3-D%02d" % n for n in range(1, 8)]
    ids += list(_L3_IDEMPOTENCY)
    ids += list(_L3_LIFECYCLE)
    return ids


class TestBuildL3:
    def test_22_l3_checks_built(self, builder):
        checks = builder.build_l3()
        assert len(checks) == 22
        assert set(checks) == set(_l3_ids())

    def test_all_l3_all_passed(self, all_checks, context):
        for cid in _l3_ids():
            r = all_checks[cid].execute(context)
            assert r.passed is True, "%s: %s" % (cid, r.details)

    def test_metadata_matches_catalog(self, all_checks, catalog):
        for cid in _l3_ids():
            check = all_checks[cid]
            md = catalog.get(cid)
            assert check.check_id == md.check_id
            assert check.evidence_type.value == md.evidence_type.value


class TestL3CoverageChecks:
    def test_determinism_uses_coverage_check(self, builder):
        checks = builder.build_l3()
        for n in range(1, 8):
            cid = "L3-D%02d" % n
            assert isinstance(checks[cid], _beh.BehavioralTestCoverageCheck)

    def test_idempotency_uses_coverage_check(self, builder):
        checks = builder.build_l3()
        for cid in _L3_IDEMPOTENCY:
            assert isinstance(checks[cid], _beh.BehavioralTestCoverageCheck)

    def test_lifecycle_uses_coverage_check(self, builder):
        checks = builder.build_l3()
        for cid in _L3_LIFECYCLE:
            assert isinstance(checks[cid], _beh.BehavioralTestCoverageCheck)

    def test_isolation_unit_requirements_match_units(self, all_checks,
                                                     context):
        """IS03 requires isolation coverage for every discovered unit."""
        r = all_checks["L3-IS03"].execute(context)
        assert set(r.evidence["unit_requirements"]) == set(
            ("citizen_host", "capability_manager", "discovery_resolver",
             "contract_enforcer", "approval_coordinator",
             "execution_scheduler", "audit_recorder"))


class TestL3ImportRules:
    def test_is01_cross_unit_check_type(self, builder):
        assert isinstance(builder.build_l3()["L3-IS01"],
                          _beh.ImportIsolationCheck)

    def test_is02_presentation_check_type(self, builder):
        assert isinstance(builder.build_l3()["L3-IS02"],
                          _beh.ImportIsolationCheck)

    def test_is01_no_cross_unit_imports(self, all_checks, context):
        r = all_checks["L3-IS01"].execute(context)
        assert r.passed is True
        assert r.evidence["violations"] == []

    def test_is02_no_presentation_imports(self, all_checks, context):
        r = all_checks["L3-IS02"].execute(context)
        assert r.passed is True
        assert r.evidence["violations"] == []

    def test_units_derived_from_snapshot(self, all_checks, context):
        r = all_checks["L3-IS01"].execute(context)
        assert isinstance(r.evidence["units"], list)
        assert len(r.evidence["units"]) == 7


class TestL3IndependentTestability:
    def test_is04_each_unit_independently_testable(self, all_checks, context):
        r = all_checks["L3-IS04"].execute(context)
        assert r.passed is True
        assert r.evidence["unmet"] == []

    def test_is04_check_type(self, builder):
        assert isinstance(builder.build_l3()["L3-IS04"],
                          _beh.IndependentTestabilityCheck)


class TestL3Determinism:
    def test_execution_deterministic(self, all_checks, context):
        for cid in _l3_ids():
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(context)
            assert r1.passed == r2.passed
            assert r1.evidence == r2.evidence
