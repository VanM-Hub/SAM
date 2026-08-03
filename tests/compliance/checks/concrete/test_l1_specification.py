"""L1 specification checker tests (P1-008 Batch 2)."""

import pytest

from sam.compliance.checks.concrete.builder import _L1_SYMBOLS, _new
from sam.compliance.checks.concrete import source_required as _src


@pytest.fixture
def l1_ids():
    return sorted(_L1_SYMBOLS)


class TestBuildL1:
    def test_40_l1_checks_built(self, builder):
        checks = builder.build_l1()
        assert len(checks) == 40
        assert set(checks) == set(_L1_SYMBOLS)

    def test_all_l1_all_passed(self, all_checks, context):
        """Every concrete L1 check passes on the real repo (PASS expected)."""
        for cid, check in all_checks.items():
            if not cid.startswith("L1"):
                continue
            r = check.execute(context)
            assert r.passed is True, "%s: %s" % (cid, r.details)

    def test_metadata_matches_catalog(self, all_checks, catalog, l1_ids):
        for cid in l1_ids:
            check = all_checks[cid]
            md = catalog.get(cid)
            assert check.check_id == md.check_id
            assert check.level.value == md.level.value
            assert check.category.value == md.category.value
            assert check.description == md.description
            assert check.baseline_ref == md.baseline_ref


class TestL1Symbols:
    def test_symbols_nonempty(self):
        for cid, symbols in _L1_SYMBOLS.items():
            assert symbols, cid
            for s in symbols:
                assert s, ("empty symbol for %s" % cid)

    def test_checker_is_source_presence(self, builder):
        checks = builder.build_l1()
        for cid, check in checks.items():
            assert isinstance(check, _src.SourceSymbolPresenceCheck), cid


class TestL1Determinism:
    def test_execution_deterministic(self, all_checks, context, l1_ids):
        for cid in l1_ids:
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(context)
            assert r1.passed == r2.passed
            assert r1.evidence == r2.evidence
