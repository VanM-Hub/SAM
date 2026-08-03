"""L4 system checker tests (P1-008 Batch 5)."""

import pytest

from sam.compliance.checks.concrete.system_level import (
    InvariantCheck, ConstraintCheck,
)
from sam.compliance.checks.concrete import system_level as _sys


def _l4_ids():
    return ["L4-01", "L4-02", "L4-03", "L4-04",
            "L4-05", "L4-06", "L4-07", "L4-08"]


class TestBuildL4:
    def test_8_l4_checks_built(self, builder):
        checks = builder.build_l4()
        assert len(checks) == 8
        assert set(checks) == set(_l4_ids())

    def test_all_l4_all_passed(self, all_checks, context):
        for cid in _l4_ids():
            r = all_checks[cid].execute(context)
            assert r.passed is True, "%s: %s" % (cid, r.details)

    def test_metadata_matches_catalog(self, all_checks, catalog):
        for cid in _l4_ids():
            check = all_checks[cid]
            md = catalog.get(cid)
            assert check.check_id == md.check_id
            assert check.evidence_type.value == md.evidence_type.value


class TestL4EvidenceMaps:
    def test_27_invariants(self):
        assert len(InvariantCheck._evidence_map) == 27
        ids = set(InvariantCheck._evidence_map)
        assert all(k.startswith("I") for k in ids)
        assert all(InvariantCheck._evidence_map[k] for k in ids)

    def test_30_constraints(self):
        # Section 5 enumerates 41 numbered constraints (S6 + B14 + A7 +
        # V4 + F5 + BD5). The narrative "30 constraints" in R5-001 is a
        # loose summary; the authoritative table defines 41 actual rows.
        assert len(ConstraintCheck._evidence_map) == 41
        ids = set(ConstraintCheck._evidence_map)
        assert all(v for v in ConstraintCheck._evidence_map.values())


class TestL4SystemProperties:
    def test_l4_06_acyclic(self, all_checks, context):
        r = all_checks["L4-06"].execute(context)
        assert r.passed is True
        assert r.evidence["cycle"] is None

    def test_l4_06_edges_are_units(self, all_checks, context):
        r = all_checks["L4-06"].execute(context)
        assert set(r.evidence["units"]) == {
            "citizen_host", "capability_manager", "discovery_resolver",
            "contract_enforcer", "approval_coordinator",
            "execution_scheduler", "audit_recorder",
        }

    def test_l4_08_linear_chain(self, all_checks, context):
        r = all_checks["L4-08"].execute(context)
        assert r.passed is True
        assert r.evidence["chain"] == [
            "citizen_host", "capability_manager", "discovery_resolver",
            "contract_enforcer", "approval_coordinator",
            "execution_scheduler", "audit_recorder",
        ]

    def test_l4_02_no_skips_in_runtime(self, all_checks, context):
        r = all_checks["L4-02"].execute(context)
        assert r.passed is True
        assert r.evidence["violations"] == []

    def test_l4_07_boundaries_enforced(self, all_checks, context):
        r = all_checks["L4-07"].execute(context)
        assert r.passed is True
        assert r.evidence["third_party"] == []


class TestL4Determinism:
    def test_execution_deterministic(self, all_checks, context):
        for cid in _l4_ids():
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(context)
            assert r1.passed == r2.passed
            assert r1.evidence == r2.evidence
