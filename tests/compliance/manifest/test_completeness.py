"""Completeness + uniqueness tests for the Compliance Manifest (P1-005).

Verifies that the loaded manifest contains exactly the 99 catalog
checks, each exactly once (no missing, no duplicate).
"""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import (
    ManifestLoader, ManifestValidator, ComplianceManifest, ManifestError,
)


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def manifest(catalog):
    return ManifestLoader(catalog).load()


class TestCompleteness:
    def test_manifest_has_99_entries(self, manifest):
        assert manifest.count() == 99

    def test_all_catalog_checks_present(self, catalog, manifest):
        catalog_ids = {c.check_id for c in catalog.list_all()}
        manifest_ids = set(manifest.check_ids())
        assert manifest_ids == catalog_ids

    def test_no_missing_checks(self, catalog, manifest):
        catalog_ids = {c.check_id for c in catalog.list_all()}
        manifest_ids = set(manifest.check_ids())
        assert catalog_ids - manifest_ids == set()

    def test_no_duplicate_checks(self, manifest):
        ids = manifest.check_ids()
        assert len(ids) == len(set(ids))

    def test_every_level_represented(self, manifest):
        """All 5 levels have at least one entry."""
        levels = set()
        for cid in manifest.check_ids():
            levels.add(cid[0:2])
        assert {"L0", "L1", "L2", "L3", "L4"} <= levels

    def test_all_entries_have_checker_class(self, manifest):
        for entry in manifest.entries():
            assert entry.checker_class, "Entry %s missing checker_class" % entry.check_id


class TestUniqueness:
    def test_duplicate_id_raises(self):
        from sam.compliance.manifest import ManifestEntry
        e1 = ManifestEntry(check_id="L0-01")
        e2 = ManifestEntry(check_id="L0-01", enabled=False)
        with pytest.raises(ManifestError):
            ComplianceManifest([e1, e2])

    def test_get_unique_entry(self, manifest):
        entry = manifest.get("L1-C01")
        assert entry is not None
        assert entry.check_id == "L1-C01"


class TestValidateCompleteness:
    def test_default_manifest_valid(self, catalog, manifest):
        result = ManifestValidator(catalog).validate(manifest)
        assert result.valid, "Default manifest should be valid"
        assert result.issues == []

    def test_missing_check_reported(self, catalog, manifest):
        from sam.compliance.manifest import ManifestEntry
        # Drop one check to simulate a missing catalog entry
        ids = [e.check_id for e in manifest.entries() if e.check_id not in ("L0-01",)]
        entries = [ManifestEntry(check_id=cid) for cid in ids]
        bad = ComplianceManifest(entries)
        result = ManifestValidator(catalog).validate(bad)
        assert not result.valid
        assert "missing" in result.error_categories()
