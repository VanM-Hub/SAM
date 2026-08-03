"""Validation tests for the Compliance Manifest (P1-005).

Verifies ManifestValidator reports: missing, duplicate, orphan,
unknown_dependency, unknown_checker, cycle.
"""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import (
    ManifestLoader, ManifestValidator, ManifestEntry, ComplianceManifest,
)


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def manifest(catalog):
    return ManifestLoader(catalog).load()


class TestValidationCategories:
    def test_default_valid(self, catalog, manifest):
        result = ManifestValidator(catalog).validate(manifest)
        assert result.valid
        assert result.issues == []

    def test_missing_check(self, catalog, manifest):
        ids = [e.check_id for e in manifest.entries() if e.check_id != "L0-01"]
        bad = ComplianceManifest([ManifestEntry(check_id=cid) for cid in ids])
        result = ManifestValidator(catalog).validate(bad)
        assert "missing" in result.error_categories()

    def test_orphan_entry(self, catalog, manifest):
        entries = list(manifest.entries())
        entries.append(ManifestEntry(check_id="NO-SUCH-CHECK"))
        bad = ComplianceManifest(entries)
        result = ManifestValidator(catalog).validate(bad)
        assert "orphan" in result.error_categories()

    def test_unknown_dependency(self, catalog, manifest):
        new = []
        for e in manifest.entries():
            deps = list(e.dependencies)
            if e.check_id == "L0-01":
                deps.append("GHOST-DEP")
            new.append(ManifestEntry(
                check_id=e.check_id, enabled=e.enabled,
                execution_order=e.execution_order,
                checker_class=e.checker_class,
                configuration=dict(e.configuration),
                timeout=e.timeout, retry_policy=e.retry_policy,
                severity=e.severity, dependencies=deps, tags=list(e.tags)))
        bad = ComplianceManifest(new)
        result = ManifestValidator(catalog).validate(bad)
        assert "unknown_dependency" in result.error_categories()

    def test_unknown_checker(self, catalog, manifest):
        new = []
        for e in manifest.entries():
            ck = e.checker_class
            if e.check_id == "L0-01":
                ck = "NoSuchCheckerClass"
            new.append(ManifestEntry(
                check_id=e.check_id, enabled=e.enabled,
                execution_order=e.execution_order, checker_class=ck,
                configuration=dict(e.configuration),
                timeout=e.timeout, retry_policy=e.retry_policy,
                severity=e.severity, dependencies=list(e.dependencies),
                tags=list(e.tags)))
        bad = ComplianceManifest(new)
        result = ManifestValidator(catalog).validate(bad)
        assert "unknown_checker" in result.error_categories()

    def test_cycle(self, catalog, manifest):
        new = []
        for e in manifest.entries():
            deps = list(e.dependencies)
            if e.check_id == "L0-01":
                deps.append("L0-02")
            if e.check_id == "L0-02":
                deps.append("L0-01")
            new.append(ManifestEntry(
                check_id=e.check_id, enabled=e.enabled,
                execution_order=e.execution_order,
                checker_class=e.checker_class,
                configuration=dict(e.configuration),
                timeout=e.timeout, retry_policy=e.retry_policy,
                severity=e.severity, dependencies=deps, tags=list(e.tags)))
        bad = ComplianceManifest(new)
        result = ManifestValidator(catalog).validate(bad)
        assert "cycle" in result.error_categories()

    def test_issues_expose_category_and_message(self, catalog, manifest):
        ids = [e.check_id for e in manifest.entries() if e.check_id != "L0-01"]
        bad = ComplianceManifest([ManifestEntry(check_id=cid) for cid in ids])
        result = ManifestValidator(catalog).validate(bad)
        assert len(result.issues) >= 1
        issue = result.issues[0]
        assert issue.category
        assert issue.message

    def test_error_categories_dedup(self, catalog, manifest):
        """Multiple issues of same category collapse to one category."""
        ids = [e.check_id for e in manifest.entries()
               if e.check_id not in ("L0-01", "L0-02")]
        bad = ComplianceManifest([ManifestEntry(check_id=cid) for cid in ids])
        result = ManifestValidator(catalog).validate(bad)
        assert result.error_categories().count("missing") == 1
