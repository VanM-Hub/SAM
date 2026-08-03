"""Serialization + determinism tests for the Compliance Manifest (P1-005).

Verifies lossless JSON/dict round-trip and deterministic output.
"""

import json
import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import (
    ManifestLoader, ManifestSerializer, ManifestEntry, ComplianceManifest,
)
from sam.compliance.models import Severity


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def manifest(catalog):
    return ManifestLoader(catalog).load()


@pytest.fixture
def serializer():
    return ManifestSerializer()


class TestSerialization:
    def test_serialize_returns_99_dicts(self, serializer, manifest):
        data = serializer.serialize(manifest)
        assert len(data) == 99

    def test_dict_has_all_keys(self, serializer, manifest):
        data = serializer.serialize(manifest)
        required = {"check_id", "enabled", "execution_order", "checker_class",
                    "configuration", "timeout", "retry_policy", "severity",
                    "dependencies", "tags"}
        for item in data:
            assert required <= set(item.keys()), item

    def test_roundtrip_preserves_ids(self, serializer, manifest):
        m2 = serializer.deserialize(serializer.serialize(manifest))
        assert m2.check_ids() == manifest.check_ids()

    def test_to_json_is_valid_json(self, serializer, manifest):
        text = serializer.to_json(manifest)
        parsed = json.loads(text)  # must not raise
        assert isinstance(parsed, list)
        assert len(parsed) == 99

    def test_from_json_roundtrip(self, serializer, manifest):
        m2 = serializer.from_json(serializer.to_json(manifest))
        assert m2.count() == 99
        assert m2.check_ids() == manifest.check_ids()

    def test_enabled_flag_roundtrip(self, catalog, serializer):
        m = ManifestLoader(catalog).load(
            overrides={"L3-D01": {"enabled": False}})
        m2 = serializer.deserialize(serializer.serialize(m))
        assert m2.get("L3-D01").enabled is False
        assert m2.get("L3-D02").enabled is True

    def test_dependencies_roundtrip(self, serializer):
        entries = [
            ManifestEntry(check_id="A", dependencies=["Z"]),
            ManifestEntry(check_id="Z", dependencies=[]),
        ]
        m = ComplianceManifest(entries)
        m2 = serializer.deserialize(serializer.serialize(m))
        assert m2.get("A").dependencies == ["Z"]

    def test_severity_roundtrip(self, serializer):
        entries = [ManifestEntry(check_id="A", severity=Severity.CRITICAL)]
        m = ComplianceManifest(entries)
        m2 = serializer.deserialize(serializer.serialize(m))
        assert m2.get("A").severity == Severity.CRITICAL

    def test_configuration_roundtrip(self, serializer):
        entries = [ManifestEntry(check_id="A", configuration={"path": "x.py"})]
        m = ComplianceManifest(entries)
        m2 = serializer.deserialize(serializer.serialize(m))
        assert m2.get("A").configuration == {"path": "x.py"}


class TestDeterminism:
    def test_serialization_deterministic(self, serializer, manifest):
        a = serializer.to_json(manifest)
        b = serializer.to_json(manifest)
        assert a == b

    def test_serialization_stable_across_instances(self, catalog):
        m1 = ManifestLoader(catalog).load()
        m2 = ManifestLoader(catalog).load()
        assert ManifestSerializer().to_json(m1) == \
               ManifestSerializer().to_json(m2)

    def test_ordered_deterministic(self, manifest):
        o1 = [e.check_id for e in manifest.ordered()]
        o2 = [e.check_id for e in manifest.ordered()]
        assert o1 == o2

    def test_execution_order_sequential(self, manifest):
        """Default loader assigns 0..98 execution_order."""
        orders = sorted(e.execution_order for e in manifest.entries())
        assert orders == list(range(99))
