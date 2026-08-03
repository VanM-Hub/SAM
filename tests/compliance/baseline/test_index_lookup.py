"""Index + lookup tests for the Compliance Baseline (P1-007)."""

import pytest

from sam.compliance.baseline import BaselineIndex


class TestIndexBuild:
    def test_index_len_equals_snapshot(self, snapshot, index):
        assert len(index) == snapshot.count

    def test_by_file_id_found(self, snapshot, index):
        first = snapshot.files()[0]
        assert index.by_file_id(first.file_id) is not None

    def test_by_file_id_missing(self, index):
        assert index.by_file_id("NOPE") is None

    def test_by_path_found(self, snapshot, index):
        first = snapshot.files()[0]
        assert index.by_path(first.relative_path) is not None

    def test_by_path_missing(self, index):
        assert index.by_path("does/not/exist.py") is None

    def test_types_sorted(self, index):
        assert index.types() == sorted(index.types())


class TestLookup:
    def test_find_by_file_id(self, snapshot):
        first = snapshot.files()[0]
        assert len(snapshot.find(first.file_id)) == 1

    def test_find_by_path_prefix(self, snapshot):
        hits = snapshot.find("docs/compliance")
        assert len(hits) >= 6
        for e in hits:
            assert e.relative_path.startswith("docs/compliance")

    def test_exists_true_false(self, snapshot):
        first = snapshot.files()[0]
        assert snapshot.exists(first.file_id)
        assert not snapshot.exists("TOTALLY_MISSING_ID")

    def test_checksum(self, snapshot):
        first = snapshot.files()[0]
        assert len(snapshot.checksum(first.file_id)) == 64
        assert snapshot.checksum("NOPE") is None

    def test_contains(self, snapshot):
        first = snapshot.files()[0]
        assert first.file_id in snapshot
        assert "NOPE" not in snapshot

    def test_get_returns_entry(self, snapshot):
        first = snapshot.files()[0]
        assert snapshot.get(first.file_id).file_id == first.file_id


class TestSelection:
    def test_files_sorted(self, snapshot):
        ids = [e.file_id for e in snapshot.files()]
        assert ids == sorted(ids)

    def test_documents_are_document_types(self, snapshot):
        for e in snapshot.documents():
            assert e.document_type in {
                "foundation", "specification", "adr", "runtime",
                "engineering", "blueprint", "compliance", "architecture",
            }

    def test_source_files_under_src(self, snapshot):
        for e in snapshot.source_files():
            assert e.relative_path.startswith("src/")

    def test_test_files_under_tests(self, snapshot):
        for e in snapshot.test_files():
            assert e.relative_path.startswith("tests/")

    def test_by_type_sort(self, snapshot):
        entries = snapshot.by_type("adr")
        ids = [e.file_id for e in entries]
        assert ids == sorted(ids)

    def test_by_authority(self, snapshot):
        entries = snapshot.by_authority("CONSTITUTION")
        assert len(entries) >= 1
        for e in entries:
            assert e.authority == "CONSTITUTION"


class TestIndexSelection:
    def test_index_by_type(self, index):
        entries = index.by_type("source")
        assert len(entries) >= 1

    def test_index_by_authority(self, index):
        assert len(index.by_authority("ADR")) >= 1

    def test_index_authorities_sorted(self, index):
        assert index.authorities() == sorted(index.authorities())
