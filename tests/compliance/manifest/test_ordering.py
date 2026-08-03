"""Ordering + dependency resolution tests for the Compliance Manifest (P1-005).

Verifies deterministic execution order, topological ordering,
dependency graph acyclicity, and candidate reliability.
"""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import (
    ManifestLoader, ManifestValidator, ManifestEntry, ComplianceManifest,
    ManifestError,
)


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def manifest(catalog):
    return ManifestLoader(catalog).load()


class TestOrdering:
    def test_default_order_is_deterministic(self, manifest):
        o1 = manifest.ordered()
        o2 = manifest.ordered()
        assert [e.check_id for e in o1] == [e.check_id for e in o2]

    def test_ordered_has_99(self, manifest):
        assert len(manifest.ordered()) == 99

    def test_entries_sorted_by_execution_order(self, manifest):
        """Default manifest should have deterministic (order, id) order."""
        entries = manifest.entries()
        for i in range(1, len(entries)):
            a = (entries[i - 1].execution_order, entries[i - 1].check_id)
            b = (entries[i].execution_order, entries[i].check_id)
            assert a <= b

    def test_no_conditional_ordering(self, manifest):
        """ordered() must not depend on external/callable state —
        only on execution_order + id (deterministic, no conditionals)."""
        o1 = manifest.ordered()
        o2 = manifest.ordered()
        assert [e.check_id for e in o1] == [e.check_id for e in o2]

    def test_no_random_ordering(self, manifest):
        """Repeated calls must be stable across instances."""
        m2 = ManifestLoader(ComplianceCheckCatalog()).load()
        assert [e.check_id for e in manifest.ordered()] == \
               [e.check_id for e in m2.ordered()]

    def test_duplicate_order_still_deterministic(self, catalog):
        """Two entries with same order disambiguate by check_id."""
        entries = [
            ManifestEntry(check_id="L0-01", execution_order=5),
            ManifestEntry(check_id="L0-02", execution_order=5),
        ]
        m = ComplianceManifest(entries)
        ids = [e.check_id for e in m.ordered()]
        assert ids == ["L0-01", "L0-02"]  # alphabetical tie-break


class TestDependencyResolution:
    def _build_dep_manifest(self):
        """A->B->C diamond-ish dependency graph, all acyclic."""
        entries = [
            ManifestEntry(check_id="A", execution_order=3, dependencies=[]),
            ManifestEntry(check_id="B", execution_order=2, dependencies=["A"]),
            ManifestEntry(check_id="C", execution_order=1, dependencies=["A"]),
            ManifestEntry(check_id="D", execution_order=0, dependencies=["B", "C"]),
        ]
        return ComplianceManifest(entries)

    def test_resolve_dependencies_transitive(self):
        m = self._build_dep_manifest()
        deps = m.resolve_dependencies("D")
        ids = {e.check_id for e in deps}
        assert ids == {"A", "B", "C"}

    def test_ordered_respects_dependencies(self):
        m = self._build_dep_manifest()
        ordered = [e.check_id for e in m.ordered()]
        idx = {cid: i for i, cid in enumerate(ordered)}
        # A must come before B and C; B and C before D
        assert idx["A"] < idx["B"]
        assert idx["A"] < idx["C"]
        assert idx["B"] < idx["D"]
        assert idx["C"] < idx["D"]

    def test_default_manifest_graph_acyclic(self, catalog, manifest):
        result = ManifestValidator(catalog).validate(manifest)
        assert "cycle" not in result.error_categories()

    def test_cycle_detected(self, catalog, manifest):
        """Introducing a cycle must be reported."""
        # L0-01 -> L0-02 and L0-02 -> L0-01
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

    def test_resolve_unknown_raises(self, manifest):
        with pytest.raises(ManifestError):
            manifest.resolve_dependencies("NOPE")


class TestEnabledDisabled:
    def test_default_all_enabled(self, manifest):
        assert len(manifest.enabled()) == 99
        assert len(manifest.disabled()) == 0

    def test_disabling_works(self, catalog):
        m = ManifestLoader(catalog).load(
            overrides={"L2-02": {"enabled": False}})
        assert len(m.enabled()) == 98
        assert len(m.disabled()) == 1
        assert m.disabled()[0].check_id == "L2-02"
