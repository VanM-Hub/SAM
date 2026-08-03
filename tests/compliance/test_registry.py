"""Tests for ComplianceRegistry."""

import pytest
from sam.compliance import (
    ComplianceRegistry,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
)
from sam.compliance.exceptions.compliance_errors import DuplicateCheckError, CheckNotFoundError


def _make_check(check_id, level=ComplianceLevel.L0_STRUCTURAL, category=None,
                evidence_type=None, severity=None):
    return ComplianceCheck(
        check_id=check_id,
        level=level,
        category=category or ComplianceCategory.RUNTIME_UNITS,
        description="Test check %s" % check_id,
        evidence_type=evidence_type or EvidenceType.FILE_EXISTS,
        severity=severity or Severity.MAJOR,
        baseline_ref="TEST_REF",
    )


class TestRegistryBasic:
    """Basic registry operations."""

    def test_register_single(self):
        registry = ComplianceRegistry()
        check = _make_check("T01")
        registry.register(check)
        assert registry.count() == 1

    def test_register_duplicate_raises(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        with pytest.raises(DuplicateCheckError):
            registry.register(_make_check("T01"))

    def test_unregister_existing(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        result = registry.unregister("T01")
        assert result is True
        assert registry.count() == 0

    def test_unregister_nonexistent(self):
        registry = ComplianceRegistry()
        result = registry.unregister("T99")
        assert result is False

    def test_find_existing(self):
        registry = ComplianceRegistry()
        check = _make_check("T01")
        registry.register(check)
        found = registry.find("T01")
        assert found is not None
        assert found.check_id == "T01"

    def test_find_nonexistent(self):
        registry = ComplianceRegistry()
        found = registry.find("T99")
        assert found is None

    def test_get_existing(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        check = registry.get("T01")
        assert check.check_id == "T01"

    def test_get_nonexistent_raises(self):
        registry = ComplianceRegistry()
        with pytest.raises(CheckNotFoundError):
            registry.get("T99")


class TestRegistryBatch:
    """Batch registration operations."""

    def test_register_all(self):
        registry = ComplianceRegistry()
        checks = [_make_check("T%02d" % i) for i in range(1, 6)]
        registry.register_all(checks)
        assert registry.count() == 5

    def test_register_all_duplicate_raises(self):
        registry = ComplianceRegistry()
        checks = [_make_check("T01"), _make_check("T01")]
        with pytest.raises(DuplicateCheckError):
            registry.register_all(checks)

    def test_register_all_duplicate_with_existing(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        checks = [_make_check("T01"), _make_check("T02")]
        with pytest.raises(DuplicateCheckError):
            registry.register_all(checks)


class TestRegistryListing:
    """List and grouping operations."""

    def test_list_all_sorted(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("Z99"))
        registry.register(_make_check("A01"))
        registry.register(_make_check("M50"))
        all_checks = registry.list_all()
        ids = [c.check_id for c in all_checks]
        assert ids == ["A01", "M50", "Z99"]

    def test_list_by_level(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", level=ComplianceLevel.L0_STRUCTURAL))
        registry.register(_make_check("T02", level=ComplianceLevel.L1_SPECIFICATION))
        registry.register(_make_check("T03", level=ComplianceLevel.L0_STRUCTURAL))

        l0 = registry.list_by_level(ComplianceLevel.L0_STRUCTURAL)
        assert len(l0) == 2
        assert all(c.level == ComplianceLevel.L0_STRUCTURAL for c in l0)

    def test_list_by_category(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", category=ComplianceCategory.ADR))
        registry.register(_make_check("T02", category=ComplianceCategory.FOUNDATION))
        registry.register(_make_check("T03", category=ComplianceCategory.ADR))

        adr = registry.list_by_category(ComplianceCategory.ADR)
        assert len(adr) == 2
        assert all(c.category == ComplianceCategory.ADR for c in adr)

    def test_group_by_level(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", level=ComplianceLevel.L0_STRUCTURAL))
        registry.register(_make_check("T02", level=ComplianceLevel.L4_SYSTEM))

        grouped = registry.group_by_level()
        assert len(grouped) == ComplianceLevel.count()
        assert len(grouped[ComplianceLevel.L0_STRUCTURAL]) == 1
        assert len(grouped[ComplianceLevel.L1_SPECIFICATION]) == 0
        assert len(grouped[ComplianceLevel.L4_SYSTEM]) == 1

    def test_group_by_category(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", category=ComplianceCategory.FOUNDATION))

        grouped = registry.group_by_category()
        assert len(grouped) == ComplianceCategory.count()
        assert len(grouped[ComplianceCategory.FOUNDATION]) == 1
        assert len(grouped[ComplianceCategory.TESTING]) == 0


class TestRegistryQuery:
    """Advanced query operations."""

    def test_count_by_level(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", level=ComplianceLevel.L2_ADR))
        registry.register(_make_check("T02", level=ComplianceLevel.L2_ADR))
        assert registry.count_by_level(ComplianceLevel.L2_ADR) == 2
        assert registry.count_by_level(ComplianceLevel.L0_STRUCTURAL) == 0

    def test_count_by_category(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01", category=ComplianceCategory.DESIGN))
        assert registry.count_by_category(ComplianceCategory.DESIGN) == 1
        assert registry.count_by_category(ComplianceCategory.ENGINEERING) == 0

    def test_check_ids(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("C"))
        registry.register(_make_check("A"))
        registry.register(_make_check("B"))
        ids = registry.check_ids()
        assert ids == ["A", "B", "C"]

    def test_contains(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        assert "T01" in registry
        assert "T99" not in registry


class TestRegistryLifecycle:
    """Registry lifecycle operations."""

    def test_clear(self):
        registry = ComplianceRegistry()
        registry.register(_make_check("T01"))
        registry.register(_make_check("T02"))
        registry.clear()
        assert registry.count() == 0
        assert registry.is_empty()

    def test_is_empty(self):
        registry = ComplianceRegistry()
        assert registry.is_empty()
        registry.register(_make_check("T01"))
        assert not registry.is_empty()

    def test_len(self):
        registry = ComplianceRegistry()
        assert len(registry) == 0
        registry.register(_make_check("T01"))
        assert len(registry) == 1


class TestRegistryDeterminism:
    """Registry must be deterministic."""

    def test_list_all_deterministic(self):
        r1 = ComplianceRegistry()
        r2 = ComplianceRegistry()
        ids = ["Z", "A", "M", "Q"]
        for cid in ids:
            r1.register(_make_check(cid))
            r2.register(_make_check(cid))

        assert [c.check_id for c in r1.list_all()] == ["A", "M", "Q", "Z"]
        assert [c.check_id for c in r2.list_all()] == ["A", "M", "Q", "Z"]

    def test_group_deterministic(self):
        r1 = ComplianceRegistry()
        r2 = ComplianceRegistry()
        r1.register(_make_check("Z01", level=ComplianceLevel.L0_STRUCTURAL))
        r1.register(_make_check("A01", level=ComplianceLevel.L0_STRUCTURAL))
        r2.register(_make_check("Z01", level=ComplianceLevel.L0_STRUCTURAL))
        r2.register(_make_check("A01", level=ComplianceLevel.L0_STRUCTURAL))

        g1 = r1.group_by_level()
        g2 = r2.group_by_level()
        ids1 = [c.check_id for c in g1[ComplianceLevel.L0_STRUCTURAL]]
        ids2 = [c.check_id for c in g2[ComplianceLevel.L0_STRUCTURAL]]
        assert ids1 == ids2 == ["A01", "Z01"]
