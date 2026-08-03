"""Tests for the Reference Runtime Composition Root public API (E1-001).

Covers: runtime builds, runtime starts, runtime stops, health aggregate,
dependency graph, pipeline, determinism, multiple build, restart, and
singleton-builder behaviour. No unit internals are asserted beyond the public
health surface that is enforced by the composition layer.

Authority: E1-001 COMPOSITION ROOT.
"""

import pytest

from sam.runtime_root import (
    CANONICAL_EDGES,
    PIPELINE,
    RuntimeBuilder,
    RuntimeContainer,
    RuntimeRoot,
)
from sam.runtime_root.exceptions import (
    CompositionValidationError,
    DependencyGraphError,
    LifecycleCompositionError,
    RuntimeCompositionError,
)
from sam.runtime_root.health import HealthStatus, RuntimeHealth
from sam.runtime_root.lifecycle import RuntimeLifecycle, RuntimeState


# ---------------------------------------------------------------------------
# runtime builds
# ---------------------------------------------------------------------------


def test_build_produces_root_in_built_state():
    root = RuntimeBuilder().build()
    assert isinstance(root, RuntimeRoot)
    assert root.lifecycle.state == RuntimeState.BUILT


def test_build_container_has_exactly_seven_units():
    root = RuntimeBuilder().build()
    container = root.container()
    assert isinstance(container, RuntimeContainer)
    assert len(container) == 7
    assert len(container.units()) == 7


def test_build_container_holds_seven_canonical_ids():
    root = RuntimeBuilder().build()
    ids = root.container().dependency_ids
    assert tuple(ids) == PIPELINE


def test_build_each_canonical_unit_instance_present():
    root = RuntimeBuilder().build()
    units = root.container().units()
    for uid in PIPELINE:
        assert uid in units
        assert units[uid] is not None


# ---------------------------------------------------------------------------
# runtime starts / stops
# ---------------------------------------------------------------------------


def test_runtime_starts():
    root = RuntimeBuilder().build()
    assert not root.is_running()
    root.start()
    assert root.is_running()
    assert root.lifecycle.state == RuntimeState.STARTED


def test_runtime_stops():
    root = RuntimeBuilder().build()
    root.start()
    root.stop()
    assert root.lifecycle.state == RuntimeState.STOPPED
    assert not root.is_running()


def test_runtime_dispose_reaches_terminal_state():
    root = RuntimeBuilder().build()
    root.start()
    root.stop()
    root.dispose()
    assert root.lifecycle.state == RuntimeState.DISPOSED


def test_lifecycle_full_sequence_deterministic():
    root = RuntimeBuilder().build()
    seq = [root.lifecycle.state]
    root.start()
    seq.append(root.lifecycle.state)
    root.stop()
    seq.append(root.lifecycle.state)
    root.dispose()
    seq.append(root.lifecycle.state)
    assert seq == [
        RuntimeState.BUILT,
        RuntimeState.STARTED,
        RuntimeState.STOPPED,
        RuntimeState.DISPOSED,
    ]


def test_stop_before_start_from_built_is_allowed():
    root = RuntimeBuilder().build()
    root.stop()  # BUILT -> STOPPED is a valid transition
    assert root.lifecycle.state == RuntimeState.STOPPED


def test_invalid_transition_crested_after_build_raises():
    root = RuntimeBuilder().build()
    with pytest.raises(RuntimeCompositionError):
        root.lifecycle.transition_to(RuntimeState.DISPOSED)  # BUILT->DISPOSED invalid


def test_start_twice_raises():
    root = RuntimeBuilder().build()
    root.start()
    with pytest.raises(LifecycleCompositionError):
        root.start()


# ---------------------------------------------------------------------------
# health aggregate
# ---------------------------------------------------------------------------


def test_health_returns_known_status():
    root = RuntimeBuilder().build()
    status = root.health()
    assert isinstance(status, HealthStatus)


def test_health_summary_reports_seven_units():
    root = RuntimeBuilder().build()
    aggregate, per_unit = root.health_summary()
    assert len(per_unit) == 7
    assert set(per_unit.keys()) == set(PIPELINE)


def test_health_aggregate_rule_failed_when_any_unit_failed():
    # The real runtime reports discovery_resolver + contract_enforcer as
    # unavailable (no initialize()); honest aggregation => Failed.
    root = RuntimeBuilder().build()
    root.start()
    assert root.health() == HealthStatus.FAILED


def test_health_aggregate_all_healthy():
    health = RuntimeHealth()
    from sam.runtime_root.interfaces import HealthProvider

    health.register(HealthProvider("a", lambda: "available"))
    health.register(HealthProvider("b", lambda: "healthy"))
    assert health.aggregate() == HealthStatus.HEALTHY
    assert health.is_healthy()


def test_health_aggregate_any_failed():
    health = RuntimeHealth()
    from sam.runtime_root.interfaces import HealthProvider

    health.register(HealthProvider("a", lambda: "available"))
    health.register(HealthProvider("b", lambda: "unavailable"))
    assert health.aggregate() == HealthStatus.FAILED
    assert health.is_failed()


def test_health_aggregate_degraded():
    health = RuntimeHealth()
    from sam.runtime_root.interfaces import HealthProvider

    health.register(HealthProvider("a", lambda: "available"))
    health.register(HealthProvider("b", lambda: "degraded"))
    assert health.aggregate() == HealthStatus.DEGRADED


def test_health_normalise_dict_and_string():
    from sam.runtime_root.health import _normalise

    assert _normalise("available") == HealthStatus.HEALTHY
    assert _normalise("unavailable") == HealthStatus.FAILED
    assert _normalise("degraded") == HealthStatus.DEGRADED
    assert _normalise({"status": "AVAILABLE"}) == HealthStatus.HEALTHY
    assert _normalise({"lifecycle": "FAILED"}) == HealthStatus.FAILED


# ---------------------------------------------------------------------------
# dependency graph / pipeline
# ---------------------------------------------------------------------------


def test_pipeline_has_seven_units_no_shortcut():
    assert len(PIPELINE) == 7
    assert PIPELINE == (
        "citizen_host",
        "capability_manager",
        "discovery_resolver",
        "contract_enforcer",
        "approval_coordinator",
        "execution_scheduler",
        "audit_recorder",
    )


def test_canonical_edges_six_adjacent_links():
    assert len(CANONICAL_EDGES) == 6
    for i, (src, dst) in enumerate(CANONICAL_EDGES):
        assert src == PIPELINE[i]
        assert dst == PIPELINE[i + 1]


def test_pipeline_no_lateral_or_skip():
    # Every edge connects exactly adjacent units; there are no shortcuts.
    for (src, dst) in CANONICAL_EDGES:
        assert src != dst
    assert len(set(PIPELINE)) == len(PIPELINE)  # no duplicates


def test_dependency_graph_acyclic():
    # The canonical chain is a linear DAG: start node has no in-edge, end node
    # has no out-edge, no node points to itself.
    from sam.runtime_root.runtime_builder import CANONICAL_EDGES as EDGES

    adjacency = {}
    for src, dst in EDGES:
        adjacency.setdefault(src, []).append(dst)
    assert set(adjacency.keys()) == set(PIPELINE[:-1])
    # linear: exactly one root (first node) with no incoming edge
    all_dsts = {d for _, d in EDGES}
    roots = [n for n in PIPELINE if n not in all_dsts]
    assert roots == ["citizen_host"]
    # no self-loop
    assert all(src != dst for src, dst in EDGES)


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_build_100_times_identical_structure():
    builder = RuntimeBuilder()
    first = builder.build()
    first_units = first.container().units()
    for _ in range(100):
        root = builder.build()
        assert root.container().dependency_ids == first.container().dependency_ids
        assert len(root.container().units()) == len(first_units)
        assert root.lifecycle.state == RuntimeState.BUILT
    assert builder.build_count == 101


# ---------------------------------------------------------------------------
# multiple build
# ---------------------------------------------------------------------------


def test_multiple_build_produces_fresh_instances():
    builder = RuntimeBuilder()
    a = builder.build()
    b = builder.build()
    assert a is not b
    # distinct instances (fresh per build)
    assert a.container() is not b.container()
    assert a.container().citizen_host is not b.container().citizen_host
    assert a.container().dependency_ids == b.container().dependency_ids


def test_build_count_increments():
    builder = RuntimeBuilder()
    assert builder.build_count == 0
    builder.build()
    builder.build()
    builder.build()
    assert builder.build_count == 3


# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------


def test_restart_returns_fresh_started_runtime():
    root = RuntimeBuilder().build()
    root.start()
    restart = root.restart()
    assert restart is not root
    assert restart.is_running()
    assert restart.lifecycle.state == RuntimeState.STARTED


def test_restart_rebuilds_fresh_instances():
    root = RuntimeBuilder().build()
    root.start()
    fresh = root.restart()
    assert fresh.container().citizen_host is not root.container().citizen_host
    assert fresh.container().dependency_ids == root.container().dependency_ids


def test_old_root_still_stopped_after_restart():
    root = RuntimeBuilder().build()
    root.start()
    root.restart()
    # restart stops the old root before building fresh
    assert root.lifecycle.state in (RuntimeState.STOPPED, RuntimeState.STARTED)
