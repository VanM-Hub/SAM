"""P1-004 Catalog test — completeness (99 checks, valid metadata)."""

from sam.compliance.catalog import ComplianceCheckCatalog, CheckLevel, CheckCategory
from sam.compliance.catalog import CheckSeverity, EvidenceType, CheckAuthority, CheckerClass


class TestCompleteness:
    def test_count_99(self):
        cat = ComplianceCheckCatalog()
        assert cat.count == 99

    def test_all_ids_unique(self):
        cat = ComplianceCheckCatalog()
        ids = [c.check_id for c in cat.list_all()]
        assert len(ids) == len(set(ids))

    def test_all_have_names(self):
        cat = ComplianceCheckCatalog()
        for c in cat:
            assert c.name, "Empty name for %s" % c.check_id

    def test_all_have_descriptions(self):
        cat = ComplianceCheckCatalog()
        for c in cat:
            assert c.description, "Empty description for %s" % c.check_id

    def test_all_have_baseline_refs(self):
        cat = ComplianceCheckCatalog()
        for c in cat:
            assert c.baseline_ref, "Empty baseline_ref for %s" % c.check_id

    def test_all_have_source_documents(self):
        cat = ComplianceCheckCatalog()
        for c in cat:
            assert c.source_document, "Empty source_document for %s" % c.check_id

    def test_all_levels_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(CheckLevel)
        for c in cat:
            assert c.level in valid, "Invalid level %s for %s" % (c.level, c.check_id)

    def test_all_categories_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(CheckCategory)
        for c in cat:
            assert c.category in valid, "Invalid category for %s" % c.check_id

    def test_all_severities_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(CheckSeverity)
        for c in cat:
            assert c.severity in valid, "Invalid severity for %s" % c.check_id

    def test_all_evidence_types_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(EvidenceType)
        for c in cat:
            assert c.evidence_type in valid, "Invalid evidence for %s" % c.check_id

    def test_all_authorities_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(CheckAuthority)
        for c in cat:
            assert c.authority in valid, "Invalid authority for %s" % c.check_id

    def test_all_checker_classes_valid(self):
        cat = ComplianceCheckCatalog()
        valid = set(CheckerClass)
        for c in cat:
            assert c.checker_class in valid, "Invalid checker for %s" % c.check_id

    def test_validate_returns_no_issues(self):
        cat = ComplianceCheckCatalog()
        issues = cat.validate()
        assert issues == [], "Validation issues: %s" % issues

    def test_level_distribution_sums_to_99(self):
        cat = ComplianceCheckCatalog()
        dist = cat.level_distribution()
        assert sum(dist.values()) == 99
        assert dist["L0"] == 12
        assert dist["L1"] == 40
        assert dist["L2"] == 17
        assert dist["L3"] == 22
        assert dist["L4"] == 8
