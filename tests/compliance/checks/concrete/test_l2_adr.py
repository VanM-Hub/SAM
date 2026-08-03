"""L2 ADR checker tests (P1-008 Batch 3)."""

import pytest

from sam.compliance.checks.concrete.builder import _L2_SYMBOLS, _L2_ABSENT
from sam.compliance.checks.concrete import source_required as _src


@pytest.fixture
def l2_ids():
    return sorted(set(_L2_SYMBOLS) | set(_L2_ABSENT))


class TestBuildL2:
    def test_17_l2_checks_built(self, builder):
        checks = builder.build_l2()
        assert len(checks) == 17
        assert set(checks) == set(_L2_SYMBOLS) | set(_L2_ABSENT)

    def test_all_l2_checks_present(self, all_checks, l2_ids):
        for cid in l2_ids:
            assert cid in all_checks

    def test_all_l2_all_passed(self, all_checks, context, l2_ids):
        for cid in l2_ids:
            r = all_checks[cid].execute(context)
            assert r.passed is True, "%s: %s" % (cid, r.details)

    def test_metadata_matches_catalog(self, all_checks, catalog, l2_ids):
        for cid in l2_ids:
            check = all_checks[cid]
            md = catalog.get(cid)
            assert check.check_id == md.check_id
            assert check.level.value == md.level.value
            assert check.evidence_type.value == md.evidence_type.value


class TestL2Types:
    def test_contains_use_presence_check(self, builder):
        checks = builder.build_l2()
        for cid in _L2_SYMBOLS:
            assert isinstance(checks[cid], _src.SourceSymbolPresenceCheck), cid

    def test_absent_use_absent_check(self, builder):
        checks = builder.build_l2()
        for cid in _L2_ABSENT:
            assert isinstance(checks[cid], _src.SourceSymbolAbsentCheck), cid

    def test_absent_scoped_to_runtime(self, builder):
        # ABSENT checks must not count the compliance tooling itself.
        checks = builder.build_l2()
        for cid in _L2_ABSENT:
            assert checks[cid]._prefixes == ("src/sam/runtime/",), cid


class TestL2Determinism:
    def test_execution_deterministic(self, all_checks, context, l2_ids):
        for cid in l2_ids:
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(context)
            assert r1.passed == r2.passed
            assert r1.evidence == r2.evidence
