"""P1-004 Catalog test — serialization and determinism."""

from sam.compliance.catalog import ComplianceCheckCatalog


class TestSerialization:
    def test_to_list_returns_99_items(self):
        cat = ComplianceCheckCatalog()
        data = cat.to_list()
        assert len(data) == 99

    def test_to_list_contains_all_keys(self):
        cat = ComplianceCheckCatalog()
        data = cat.to_list()
        required = {
            "check_id", "name", "level", "category", "severity",
            "authority", "evidence_type", "checker_class",
            "expected_verdict", "source_document", "baseline_ref",
            "description",
        }
        for item in data:
            missing = required - set(item.keys())
            assert not missing, "Missing keys %s in %s" % (missing, item["check_id"])

    def test_to_list_values_are_strings(self):
        cat = ComplianceCheckCatalog()
        data = cat.to_list()
        str_fields = {"check_id", "name", "level", "category", "severity",
                      "authority", "evidence_type", "checker_class",
                      "expected_verdict", "source_document", "baseline_ref",
                      "description"}
        for item in data:
            for field in str_fields:
                assert isinstance(item[field], str), \
                    "Field %s is not str in %s: %s" % (field, item["check_id"], type(item[field]))


class TestDeterminism:
    def test_catalog_construction_is_deterministic(self):
        cat1 = ComplianceCheckCatalog()
        cat2 = ComplianceCheckCatalog()
        ids1 = [c.check_id for c in cat1.list_all()]
        ids2 = [c.check_id for c in cat2.list_all()]
        assert ids1 == ids2

    def test_serialization_deterministic(self):
        cat1 = ComplianceCheckCatalog()
        cat2 = ComplianceCheckCatalog()
        d1 = cat1.to_list()
        d2 = cat2.to_list()
        assert d1 == d2

    def test_filtering_deterministic(self):
        from sam.compliance.catalog import CheckLevel
        cat1 = ComplianceCheckCatalog()
        cat2 = ComplianceCheckCatalog()
        ids1 = [c.check_id for c in cat1.by_level(CheckLevel.L1_SPECIFICATION)]
        ids2 = [c.check_id for c in cat2.by_level(CheckLevel.L1_SPECIFICATION)]
        assert ids1 == ids2


class TestDistribution:
    def test_level_distribution(self):
        cat = ComplianceCheckCatalog()
        dist = cat.level_distribution()
        assert dist == {"L0": 12, "L1": 40, "L2": 17, "L3": 22, "L4": 8}

    def test_category_distribution(self):
        cat = ComplianceCheckCatalog()
        dist = cat.category_distribution()
        assert dist["Specification"] == 40
        assert dist["ADR"] == 17

    def test_authority_distribution(self):
        cat = ComplianceCheckCatalog()
        dist = cat.authority_distribution()
        assert dist["Blueprint"] == 12
        assert dist["Specification"] == 47
        assert dist["ADR"] == 21

    def test_evidence_distribution(self):
        cat = ComplianceCheckCatalog()
        dist = cat.evidence_distribution()
        assert dist["SOURCE_CONTAINS"] > 0
        assert dist["FILE_EXISTS"] == 10

    def test_checker_distribution(self):
        cat = ComplianceCheckCatalog()
        dist = cat.checker_distribution()
        assert dist["SourceContainsCheck"] > 0
        assert dist["FileExistsCheck"] == 10
