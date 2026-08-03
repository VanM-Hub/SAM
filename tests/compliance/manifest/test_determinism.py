"""Determinism tests for the Compliance Manifest (P1-005).

Verifies the manifest is deterministic and does NOT support runtime
mutation: same input always produces same output, and repeated
queries never vary based on call order or external state.
"""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import (
    ManifestLoader, ManifestSerializer, ComplianceManifest, ManifestEntry,
)


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


def test_loader_is_stateless(catalog):
    """Two loads from same catalog give identical manifests."""
    m1 = ManifestLoader(catalog).load()
    m2 = ManifestLoader(catalog).load()
    assert [e.check_id for e in m1.entries()] == \
           [e.check_id for e in m2.entries()]


def test_no_runtime_mutation_entries(catalog):
    """Calling queries must not change the manifest's entry set."""
    m = ManifestLoader(catalog).load()
    before = m.check_ids()
    m.entries()
    m.enabled()
    m.disabled()
    m.ordered()
    assert m.check_ids() == before


def test_no_runtime_mutation_json(catalog):
    """Serialization must not mutate the manifest."""
    m = ManifestLoader(catalog).load()
    ids_before = m.check_ids()
    ManifestSerializer().to_json(m)
    assert m.check_ids() == ids_before


def test_manifest_entry_frozen():
    """ManifestEntry must be immutable (frozen dataclass)."""
    e = ManifestEntry(check_id="A")
    with pytest.raises(Exception):
        e.enabled = False  # frozen -> raises FrozenInstanceError


def test_manifest_duplicate_rejected():
    with pytest.raises(Exception):
        ComplianceManifest([
            ManifestEntry(check_id="A"),
            ManifestEntry(check_id="A"),
        ])


def test_same_input_same_output():
    """Determinism across two independent catalog instances."""
    m1 = ManifestLoader(ComplianceCheckCatalog()).load()
    m2 = ManifestLoader(ComplianceCheckCatalog()).load()
    assert [e.check_id for e in m1.ordered()] == \
           [e.check_id for e in m2.ordered()]
