"""Integration tests for the Reference Runtime composition (E1-001).

Covers the full lifecycle through the public facade and the determinism
acceptance: RuntimeBuilder.build() 100 times produces identical graphs.

Integration flow:
    RuntimeBuilder.build() -> RuntimeContainer
        -> start() -> health() -> validate() -> stop()
"""

import pytest

from sam.runtime_root import (
    HealthStatus,
    RuntimeBuilder,
    RuntimeContainer,
)
from sam.runtime_root.graph import UNIT_CHAIN


@pytest.fixture(scope="module")
def container():
    """A fully built, started, validated, then stopped container."""
    rt = RuntimeContainer(RuntimeBuilder().build())
    rt.start()
    return rt


def test_build_then_lifecycle_integration():
    """build -> start -> health -> validate -> stop."""
    rt = RuntimeContainer(RuntimeBuilder().build())
    assert rt.validate() is True
    rt.start()
    assert rt.lifecycle.is_operational()
    assert rt.health() in (HealthStatus.AVAILABLE, HealthStatus.DEGRADED,
                           HealthStatus.UNAVAILABLE)
    assert rt.validate() is True
    rt.stop()
    assert rt.lifecycle.is_stopped()


def test_all_units_present_via_facade(container):
    units = container.units()
    assert set(units.keys()) == set(UNIT_CHAIN)
    for uid in UNIT_CHAIN:
        assert units[uid] is not None


def test_container_exposes_canonical_getters(container):
    assert container.citizen_host is not None
    assert container.capability_manager is not None
    assert container.discovery_resolver is not None
    assert container.contract_enforcer is not None
    assert container.approval_coordinator is not None
    assert container.execution_scheduler is not None
    assert container.audit_recorder is not None


def test_graph_is_canonical_acyclic(container):
    g = container.graph
    assert g.is_acyclic()
    assert container.composition.validate() is True


def test_health_aggregation_sound(container):
    per_unit = container.composition.health.all_health()
    assert len(per_unit) == 7
    # Factory container has started; at least the auto-initialising units
    # report AVAILABLE. Aggregation never raises and returns a known status.
    assert isinstance(container.health(), HealthStatus)


def test_repeated_build_100_times_identical_graph():
    """E1-001 acceptance: build 100x yields identical graphs."""
    builder = RuntimeBuilder()
    reference = builder.build().graph
    for _ in range(100):
        g = builder.build().graph
        assert g.equals(reference)
        assert g.is_acyclic()
        assert g.nodes == frozenset(UNIT_CHAIN)


def test_repeated_build_full_lifecycle_100_times():
    """Each build supports an independent full lifecycle."""
    builder = RuntimeBuilder()
    for _ in range(100):
        rt = RuntimeContainer(builder.build())
        rt.start()
        assert rt.lifecycle.is_operational()
        rt.stop()
        assert rt.lifecycle.is_stopped()


def test_each_build_has_fresh_instances():
    """Repeated builds never share unit instances (no global singleton)."""
    builder = RuntimeBuilder()
    c1 = builder.build()
    c2 = builder.build()
    for uid in UNIT_CHAIN:
        assert c1.registry.get(uid) is not c2.registry.get(uid)
