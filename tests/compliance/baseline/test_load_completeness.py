"""Loading + completeness tests for the Compliance Baseline (P1-007)."""

import pytest

from sam.compliance.baseline import BaselineLoader, BaselineValidator


class TestLoading:
    def test_load_returns_snapshot(self, snapshot):
        assert snapshot.count > 0

    def test_default_snapshot_valid(self, snapshot):
        res = BaselineValidator(snapshot).validate(check_disk=False)
        assert res.valid
        assert len(res.issues) == 0

    def test_all_entries_have_checksum(self, snapshot):
        for e in snapshot.files():
            assert len(e.checksum) == 64  # sha256

    def test_all_entries_have_path(self, snapshot):
        for e in snapshot.files():
            assert e.relative_path

    def test_paths_posix(self, snapshot):
        for e in snapshot.files():
            assert "\\" not in e.relative_path

    def test_file_ids_unique(self, snapshot):
        ids = [e.file_id for e in snapshot.files()]
        assert len(ids) == len(set(ids))


class TestCoverage:
    def test_required_types_present(self, snapshot):
        """All 11 required baseline categories must be covered."""
        required = {
            "foundation", "specification", "adr", "runtime", "engineering",
            "blueprint", "compliance", "source", "test", "package",
        }
        types = set(snapshot.type_distribution())
        for req in required:
            assert req in types, "missing type: %s" % req

    def test_foundation_docs(self, snapshot):
        assert len(snapshot.by_type("foundation")) >= 1

    def test_specification_docs(self, snapshot):
        assert len(snapshot.by_type("specification")) >= 1

    def test_adr_docs(self, snapshot):
        assert len(snapshot.by_type("adr")) >= 1

    def test_blueprint_docs(self, snapshot):
        assert len(snapshot.by_type("blueprint")) >= 1

    def test_compliance_docs(self, snapshot):
        assert len(snapshot.by_type("compliance")) >= 1

    def test_source_files(self, snapshot):
        assert len(snapshot.source_files()) >= 1

    def test_test_files(self, snapshot):
        assert len(snapshot.test_files()) >= 1

    def test_package_files(self, snapshot):
        assert len(snapshot.by_type("package")) >= 1

    def test_document_type_has_authority(self, snapshot):
        """Document types map to an authority where applicable."""
        for t in ("foundation", "specification", "adr", "blueprint"):
            entries = snapshot.by_type(t)
            if entries:
                assert entries[0].authority is not None


class TestComplianceDocs:
    def test_p1_docs_present(self, snapshot):
        """The P1 compliance documents must all be indexed."""
        paths = {e.relative_path for e in snapshot.files()}
        expected = [
            "docs/compliance/P1-001_Runtime_Compliance_Suite.md",
            "docs/compliance/P1-002_Runtime_Compliance_Engine.md",
            "docs/compliance/P1-003_Compliance_Check_Framework.md",
            "docs/compliance/P1-004_Runtime_Compliance_Check_Catalog.md",
            "docs/compliance/P1-005_Runtime_Compliance_Manifest.md",
            "docs/compliance/P1-006_Runtime_Compliance_CLI.md",
        ]
        for p in expected:
            assert p in paths, "missing %s" % p

    def test_p1_docs_type_compliance(self, snapshot):
        for e in snapshot.by_type("compliance"):
            assert e.relative_path.startswith("docs/compliance/")
