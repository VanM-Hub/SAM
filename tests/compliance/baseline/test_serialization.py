"""Serialization + determinism tests for the Compliance Baseline (P1-007)."""

import json

import pytest

from sam.compliance.baseline import (
    BaselineSerializer, BaselineSnapshot, BaselineEntry,
)


class TestSerialization:
    def test_serialize_has_format(self, snapshot, serializer):
        d = serializer.serialize(snapshot)
        assert d["format"] == BaselineSerializer.FORMAT

    def test_serialize_entry_count(self, snapshot, serializer):
        d = serializer.serialize(snapshot)
        assert d["entry_count"] == snapshot.count

    def test_roundtrip_preserves_count(self, snapshot, serializer):
        d = serializer.serialize(snapshot)
        snap2 = serializer.deserialize(d)
        assert snap2.count == snapshot.count

    def test_roundtrip_preserves_ids(self, snapshot, serializer):
        js = serializer.to_json(snapshot)
        snap2 = serializer.from_json(js)
        assert [e.file_id for e in snap2.files()] == \
               [e.file_id for e in snapshot.files()]

    def test_roundtrip_preserves_paths(self, snapshot, serializer):
        js = serializer.to_json(snapshot)
        snap2 = serializer.from_json(js)
        assert [e.relative_path for e in snap2.files()] == \
               [e.relative_path for e in snapshot.files()]

    def test_roundtrip_preserves_checksums(self, snapshot, serializer):
        js = serializer.to_json(snapshot)
        snap2 = serializer.from_json(js)
        assert [e.checksum for e in snap2.files()] == \
               [e.checksum for e in snapshot.files()]

    def test_unsupported_format_raises(self, serializer):
        with pytest.raises(ValueError):
            serializer.deserialize({"format": "bogus", "entries": []})

    def test_json_is_valid_json(self, snapshot, serializer):
        js = serializer.to_json(snapshot)
        assert isinstance(json.loads(js), dict)

    def test_entry_to_from_dict_roundtrip(self):
        e = BaselineEntry(
            file_id="FID-TEST-001", logical_id="LID-1",
            document_type="test", authority=None,
            checksum="a" * 64, relative_path="tests/x.py",
            traceability=("FID-TEST-000",),
        )
        e2 = BaselineEntry.from_dict(e.to_dict())
        assert e2 == e


class TestDeterminism:
    def test_json_deterministic(self, snapshot, serializer):
        js1 = serializer.to_json(snapshot)
        js2 = serializer.to_json(snapshot)
        assert js1 == js2

    def test_load_deterministic_ids(self, loader, snapshot):
        snap2 = loader.load()
        assert [e.file_id for e in snap2.files()] == \
               [e.file_id for e in snapshot.files()]

    def test_load_deterministic_checksums(self, loader, snapshot):
        snap2 = loader.load()
        assert [e.checksum for e in snap2.files()] == \
               [e.checksum for e in snapshot.files()]

    def test_load_deterministic_order(self, loader, snapshot):
        snap2 = loader.load()
        assert [e.relative_path for e in snap2.files()] == \
               [e.relative_path for e in snapshot.files()]


class TestSnapshotImmutable:
    def test_duplicate_file_id_rejected(self, snapshot):
        first = snapshot.files()[0]
        dup = BaselineEntry.from_dict(first.to_dict())
        from sam.compliance.baseline import ManifestError
        with pytest.raises(ManifestError):
            BaselineSnapshot([first, dup])
