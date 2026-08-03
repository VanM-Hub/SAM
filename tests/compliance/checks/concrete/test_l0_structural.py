"""L0 structural checker tests (P1-008 Batch 1)."""

import pytest

from sam.compliance.checks.base.check_context import CheckContext


class TestL0Count:
    def test_l0_01_checks_7_units(self, all_checks, context):
        assert "L0-01" in all_checks
        r = all_checks["L0-01"].execute(context)
        assert r.passed is True
        assert r.evidence["unit_count"] == 7

    def test_l0_02_no_8th_unit(self, all_checks, context):
        r = all_checks["L0-02"].execute(context)
        assert r.passed is True
        assert r.evidence["unit_count"] == 7


class TestL0Skeleton:
    @pytest.mark.parametrize("cid,sub", [
        ("L0-03", "models"),
        ("L0-04", "interfaces"),
        ("L0-05", "services"),
        ("L0-06", "lifecycle"),
        ("L0-07", "validation"),
        ("L0-08", "exceptions"),
    ])
    def test_unit_skeleton_dir_present(self, all_checks, context, cid, sub):
        assert cid in all_checks
        r = all_checks[cid].execute(context)
        assert r.passed is True, r.details
        assert r.evidence["missing"] == []
        assert r.evidence["sub"] == sub

    def test_l0_09_state_only_for_units_with_state(self, all_checks, context):
        r = all_checks["L0-09"].execute(context)
        assert r.passed is True, r.details


class TestL0Init:
    def test_l0_10_init_present(self, all_checks, context):
        r = all_checks["L0-10"].execute(context)
        assert r.passed is True
        assert r.evidence["missing"] == []


class TestL0NoExtra:
    def test_l0_11_no_extra_top_level_dirs(self, all_checks, context):
        r = all_checks["L0-11"].execute(context)
        assert r.passed is True
        assert r.evidence["extras"] == []


class TestL0TestMirror:
    def test_l0_12_test_mirror(self, all_checks, context):
        r = all_checks["L0-12"].execute(context)
        assert r.passed is True
        assert r.evidence["missing"] == []


class TestL0Determinism:
    def test_execution_deterministic(self, all_checks, context):
        for cid in sorted(all_checks):
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(context)
            assert r1.passed == r2.passed
            assert r1.evidence == r2.evidence

    def test_different_context_same_snapshot(self, all_checks, context):
        c2 = CheckContext(
            target_path=r"D:\Project AI\SAM\src",
            options={"baseline": context.options["baseline"]},
        )
        for cid in sorted(all_checks):
            r1 = all_checks[cid].execute(context)
            r2 = all_checks[cid].execute(c2)
            assert r1.passed == r2.passed
