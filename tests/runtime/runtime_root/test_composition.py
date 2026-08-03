"""Tests for the composition layer core (E1-001): builder, composition,
container, lifecycle, dependency graph, health, registry, validator.
"""

import pytest

from sam.runtime_root.builder import RuntimeBuilder
from sam.runtime_root.composition import RuntimeComposition
from sam.runtime_root.container import RuntimeContainer
from sam.runtime_root.exceptions import (
    CompositionDefinitionError,
    CompositionValidationError,
    DependencyGraphError,
    LifecycleCompositionError,
)
from sam.runtime_root.health import HealthStatus
from sam.runtime_root.graph import UNIT_CHAIN, DependencyGraph
from sam.runtime_root.lifecycle import (
    RuntimeLifecycle,
    RuntimeState,
)
from sam.runtime_root.registry import RuntimeRegistry
from sam.runtime_root.validator import CompositionValidator


class TestRuntimeBuilder:
    def test_build_creates_7_units(self):
        comp = RuntimeBuilder().build()
        assert len(comp.registry) == 7
        assert set(comp.registry.ids()) == set(UNIT_CHAIN)

    def test_build_exactly_one_instance_per_unit(self):
        comp = RuntimeBuilder().build()
        for unit in UNIT_CHAIN:
            inst = comp.registry.get(unit)
            assert inst is not None
            # Each unit reports a recognisable health status.
            assert comp.health.unit_health(unit) in (
                HealthStatus.AVAILABLE,
                HealthStatus.DEGRADED,
                HealthStatus.UNAVAILABLE,
            )

    def test_build_returns_fresh_composition(self):
        b = RuntimeBuilder()
        c1 = b.build()
        c2 = b.build()
        assert c1 is not c2
        assert c1.registry is not c2.registry

    def test_repeated_build_identical_graph(self):
        b = RuntimeBuilder()
        g1 = b.build().graph
        g2 = b.build().graph
        assert g1.equals(g2)

    def test_registry_is_frozen_after_build(self):
        comp = RuntimeBuilder().build()
        with pytest.raises(CompositionDefinitionError):
            comp.registry.register("new_unit", object())

    def test_registry_rejects_duplicate_registration(self):
        reg = RuntimeRegistry()
        reg.register("citizen_host", object())
        with pytest.raises(CompositionDefinitionError):
            reg.register("citizen_host", object())

    def test_registry_rejects_none(self):
        reg = RuntimeRegistry()
        with pytest.raises(CompositionDefinitionError):
            reg.register("citizen_host", None)


class TestDependencyGraph:
    def test_canonical_is_line_chain(self):
        g = DependencyGraph.canonical()
        assert g.is_acyclic()
        assert g.nodes == frozenset(UNIT_CHAIN)
        edges = set(g.edges())
        for i in range(len(UNIT_CHAIN) - 1):
            assert (UNIT_CHAIN[i], UNIT_CHAIN[i + 1]) in edges

    def test_cycle_rejected(self):
        with pytest.raises(DependencyGraphError):
            DependencyGraph(
                edges=[
                    ("citizen_host", "capability_manager"),
                    ("capability_manager", "citizen_host"),
                ]
            )

    def test_non_adjacent_edge_rejected(self):
        # skip (Citizen Host -> Discovery Resolver) is not canonical.
        with pytest.raises(DependencyGraphError):
            DependencyGraph(
                edges=[("citizen_host", "discovery_resolver")]
            )

    def test_audit_recorder_is_leaf(self):
        g = DependencyGraph.canonical()
        assert g.downstream("audit_recorder") == frozenset()

    def test_graph_equality(self):
        g1 = DependencyGraph.canonical()
        g2 = DependencyGraph.canonical()
        assert g1.equals(g2)


class TestRegistry:
    def test_get_unknown_raises(self):
        reg = RuntimeRegistry()
        with pytest.raises(CompositionDefinitionError):
            reg.get("missing")

    def test_contains(self):
        reg = RuntimeRegistry()
        reg.register("citizen_host", object())
        assert reg.contains("citizen_host")
        assert not reg.contains("audit_recorder")

    def test_ids_stable_order(self):
        reg = RuntimeRegistry()
        reg.register("audit_recorder", object())
        reg.register("citizen_host", object())
        assert reg.ids() == ["audit_recorder", "citizen_host"]

    def test_validate_canonical(self):
        reg = RuntimeRegistry()
        for u in UNIT_CHAIN:
            reg.register(u, object())
        assert reg.validate_canonical() is True

    def test_validate_canonical_missing(self):
        reg = RuntimeRegistry()
        reg.register("citizen_host", object())
        with pytest.raises(CompositionDefinitionError):
            reg.validate_canonical()


class TestRuntimeLifecycle:
    def test_initial_state_created(self):
        lc = RuntimeLifecycle()
        assert lc.state == RuntimeState.CREATED

    def test_valid_transitions(self):
        lc = RuntimeLifecycle()
        lc.transition_to(RuntimeState.COMPOSED)
        lc.transition_to(RuntimeState.STARTING)
        lc.transition_to(RuntimeState.RUNNING)
        lc.transition_to(RuntimeState.STOPPING)
        lc.transition_to(RuntimeState.STOPPED)
        assert lc.state == RuntimeState.STOPPED

    def test_invalid_transition_raises(self):
        lc = RuntimeLifecycle()
        with pytest.raises(LifecycleCompositionError):
            lc.transition_to(RuntimeState.RUNNING)  # from CREATED

    def test_is_operational_only_when_running(self):
        lc = RuntimeLifecycle(RuntimeState.RUNNING)
        assert lc.is_operational()
        lc2 = RuntimeLifecycle(RuntimeState.CREATED)
        assert not lc2.is_operational()

    def test_is_stopped(self):
        assert RuntimeLifecycle(RuntimeState.STOPPED).is_stopped()
        assert RuntimeLifecycle(RuntimeState.FAILED).is_stopped()
        assert not RuntimeLifecycle(RuntimeState.RUNNING).is_stopped()


class TestHealth:
    def test_all_available(self):
        from sam.runtime_root.health import RuntimeHealth

        h = RuntimeHealth({"a": lambda: "AVAILABLE", "b": lambda: "AVAILABLE"})
        assert h.aggregate() == HealthStatus.AVAILABLE

    def test_any_unavailable(self):
        from sam.runtime_root.health import RuntimeHealth

        h = RuntimeHealth(
            {"a": lambda: "AVAILABLE", "b": lambda: "UNAVAILABLE"}
        )
        assert h.aggregate() == HealthStatus.UNAVAILABLE

    def test_degraded_when_mixed_non_unavailable(self):
        from sam.runtime_root.health import RuntimeHealth

        h = RuntimeHealth(
            {"a": lambda: "AVAILABLE", "b": lambda: "DEGRADED"}
        )
        assert h.aggregate() == HealthStatus.DEGRADED

    def test_empty_is_unavailable(self):
        from sam.runtime_root.health import RuntimeHealth

        assert RuntimeHealth().aggregate() == HealthStatus.UNAVAILABLE

    def test_unknown_health_producer_raises(self):
        from sam.runtime_root.health import RuntimeHealth

        h = RuntimeHealth({"a": lambda: "AVAILABLE"})
        with pytest.raises(CompositionDefinitionError):
            h.unit_health("missing")

    def test_aggregate_matches_unit_health(self):
        comp = RuntimeBuilder().build()
        agg = comp.health.aggregate()
        per_unit = comp.health.all_health()
        assert len(per_unit) == 7
        # Aggregate follows the deterministic rule over unit reports.
        statuses = list(per_unit.values())
        expected = (
            HealthStatus.AVAILABLE
            if all(s == HealthStatus.AVAILABLE for s in statuses)
            else (
                HealthStatus.UNAVAILABLE
                if any(s == HealthStatus.UNAVAILABLE for s in statuses)
                else HealthStatus.DEGRADED
            )
        )
        assert agg == expected


class TestCompositionLifecycle:
    def test_start_is_deterministic(self):
        comp = RuntimeBuilder().build()
        comp.start()
        assert comp.lifecycle.state == RuntimeState.RUNNING
        assert comp.lifecycle.is_operational()

    def test_stop_deterministic(self):
        comp = RuntimeBuilder().build()
        comp.start()
        comp.stop()
        assert comp.lifecycle.state == RuntimeState.STOPPED
        assert comp.lifecycle.is_stopped()

    def test_cannot_stop_before_start(self):
        comp = RuntimeBuilder().build()
        with pytest.raises(LifecycleCompositionError):
            comp.stop()  # CREATED -> STOPPING invalid

    def test_cannot_restart_after_stop(self):
        comp = RuntimeBuilder().build()
        comp.start()
        comp.stop()
        with pytest.raises(LifecycleCompositionError):
            comp.start()  # STOPPED -> COMPOSED invalid


class TestCompositionValidator:
    def test_validate_passes_after_build(self):
        comp = RuntimeBuilder().build()
        assert comp.validate() is True

    def test_validator_validates_running(self):
        comp = RuntimeBuilder().build()
        comp.start()
        assert comp.validate() is True

    def test_completeness_missing_unit(self):
        reg = RuntimeRegistry()
        # register only 6 of 7
        for u in UNIT_CHAIN[:6]:
            reg.register(u, object())
        validator = CompositionValidator(reg)
        with pytest.raises(CompositionValidationError):
            validator.check_completeness()

    def test_dependency_mismatch(self):
        reg = RuntimeRegistry()
        for u in UNIT_CHAIN:
            reg.register(u, object())
        validator = CompositionValidator(reg)
        bad = DependencyGraph(edges=[])
        with pytest.raises(CompositionValidationError):
            validator.check_dependency(bad)

    def test_lifecycle_unavailable(self):
        reg = RuntimeRegistry()
        for u in UNIT_CHAIN:
            reg.register(u, object())
        validator = CompositionValidator(reg, lifecycle=None)
        with pytest.raises(CompositionValidationError):
            validator.check_lifecycle()


class TestRuntimeContainer:
    def test_container_wraps_composition(self):
        comp = RuntimeBuilder().build()
        rt = RuntimeContainer(comp)
        assert rt.composition is comp

    def test_container_public_api(self):
        rt = RuntimeContainer(RuntimeBuilder().build())
        assert rt.validate() is True
        assert rt.health() in (HealthStatus.AVAILABLE, HealthStatus.DEGRADED,
                               HealthStatus.UNAVAILABLE)
        rt.start()
        assert rt.lifecycle.is_operational()
        rt.stop()
        assert rt.lifecycle.is_stopped()

    def test_container_unit_accessors(self):
        rt = RuntimeContainer(RuntimeBuilder().build())
        assert rt.citizen_host is not None
        assert rt.capability_manager is not None
        assert rt.discovery_resolver is not None
        assert rt.contract_enforcer is not None
        assert rt.approval_coordinator is not None
        assert rt.execution_scheduler is not None
        assert rt.audit_recorder is not None
        assert len(rt.units()) == 7
