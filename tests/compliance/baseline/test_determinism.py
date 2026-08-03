"""Determinism tests for the Compliance Baseline (P1-007)."""

import pytest

from sam.compliance.baseline import BaselineSerializer


class TestDeterminism:
    def test_repeated_load_identical(self, loader):
        s1 = loader.load()
        s2 = loader.load()
        assert [e.checksum for e in s1.files()] == \
               [e.checksum for e in s2.files()]

    def test_serialize_order_stable(self, snapshot, serializer):
        d1 = serializer.serialize(snapshot)
        d2 = serializer.serialize(snapshot)
        assert d1 == d2

    def test_selection_stable_across_loads(self, snapshot):
        source1 = [e.relative_path for e in snapshot.source_files()]
        source2 = [e.relative_path for e in snapshot.source_files()]
        assert source1 == source2

    def test_no_random_ids(self, loader):
        s1 = loader.load()
        s2 = loader.load()
        assert [e.file_id for e in s1.files()] == \
               [e.file_id for e in s2.files()]
