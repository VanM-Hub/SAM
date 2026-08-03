"""P1-004 Catalog test — lookup and filtering."""

from sam.compliance.catalog import (
    ComplianceCheckCatalog, CheckLevel, CheckCategory,
    CheckSeverity, EvidenceType, CheckAuthority, CheckerClass,
)


class TestLookup:
    def test_get_valid_id(self):
        cat = ComplianceCheckCatalog()
        c = cat.get("L1-C01")
        assert c is not None
        assert c.check_id == "L1-C01"
        assert c.level == CheckLevel.L1_SPECIFICATION

    def test_get_invalid_returns_none(self):
        cat = ComplianceCheckCatalog()
        assert cat.get("NONEXISTENT") is None

    def test_bracket_access(self):
        cat = ComplianceCheckCatalog()
        c = cat["L0-01"]
        assert c.check_id == "L0-01"

    def test_bracket_missing_raises(self):
        cat = ComplianceCheckCatalog()
        try:
            _ = cat["NO-SUCH-ID"]
            assert False, "Expected KeyError"
        except KeyError:
            pass

    def test_contains(self):
        cat = ComplianceCheckCatalog()
        assert "L1-C01" in cat
        assert "NONEXISTENT" not in cat

    def test_length(self):
        cat = ComplianceCheckCatalog()
        assert len(cat) == 99


class TestFilterByLevel:
    def test_l0(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_level(CheckLevel.L0_STRUCTURAL)
        assert len(checks) == 12

    def test_l1(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_level(CheckLevel.L1_SPECIFICATION)
        assert len(checks) == 40

    def test_l2(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_level(CheckLevel.L2_ADR)
        assert len(checks) == 17

    def test_l3(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_level(CheckLevel.L3_BEHAVIORAL)
        assert len(checks) == 22

    def test_l4(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_level(CheckLevel.L4_SYSTEM)
        assert len(checks) == 8

    def test_l1_sorted(self):
        cat = ComplianceCheckCatalog()
        ids = [c.check_id for c in cat.by_level(CheckLevel.L1_SPECIFICATION)]
        assert ids == sorted(ids)


class TestFilterByCategory:
    def test_specification_category(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_category(CheckCategory.SPECIFICATION)
        assert len(checks) == 40

    def test_adr_category(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_category(CheckCategory.ADR)
        assert len(checks) == 17

    def test_runtime_units_category(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_category(CheckCategory.RUNTIME_UNITS)
        assert len(checks) == 12

    def test_testing_category(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_category(CheckCategory.TESTING)
        assert len(checks) == 18


class TestFilterByAuthority:
    def test_blueprint_authority(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_authority(CheckAuthority.BLUEPRINT)
        assert len(checks) == 12

    def test_specification_authority(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_authority(CheckAuthority.SPECIFICATION)
        assert len(checks) == 47  # 40 L1 spec + 7 L3 lifecycle

    def test_adr_authority(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_authority(CheckAuthority.ADR)
        assert len(checks) == 21  # 17 L2 + 4 L3 idempotency

    def test_constitution_authority(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_authority(CheckAuthority.CONSTITUTION)
        assert len(checks) == 7


class TestFilterByEvidence:
    def test_source_contains(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_evidence(EvidenceType.SOURCE_CONTAINS)
        assert len(checks) > 0

    def test_file_exists(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_evidence(EvidenceType.FILE_EXISTS)
        assert len(checks) == 10  # L0-01,03-10,12

    def test_test_pass(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_evidence(EvidenceType.TEST_PASS)
        assert len(checks) == 21  # 7 det + 4 idem + 7 lc + 2 iso + 1 sys

    def test_no_unknown_evidence_type(self):
        cat = ComplianceCheckCatalog()
        for ev in EvidenceType:
            checks = cat.by_evidence(ev)
            assert isinstance(checks, list)


class TestFilterByTag:
    def test_structural_tag(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_tag("structural")
        assert len(checks) == 12

    def test_specification_tag(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_tag("specification")
        assert len(checks) == 40

    def test_adr_tag(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_tag("adr")
        assert len(checks) == 17

    def test_behavioral_tag(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_tag("behavioral")
        assert len(checks) == 22

    def test_system_tag(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_tag("system")
        assert len(checks) == 8

    def test_unknown_tag_empty(self):
        cat = ComplianceCheckCatalog()
        assert cat.by_tag("nonexistent") == []


class TestFilterBySourceDocument:
    def test_citizen_spec(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_source_document("CITIZEN_SPEC")
        assert len(checks) == 6  # 5 L1 citizen + 1 L3-LC01

    def test_adr_source(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_source_document("ADR")
        assert len(checks) == 17

    def test_constitution(self):
        cat = ComplianceCheckCatalog()
        checks = cat.by_source_document("CONSTITUTION")
        assert len(checks) == 7


class TestIteration:
    def test_iter_yields_99(self):
        cat = ComplianceCheckCatalog()
        count = sum(1 for _ in cat)
        assert count == 99

    def test_list_all_returns_99(self):
        cat = ComplianceCheckCatalog()
        assert len(cat.list_all()) == 99
