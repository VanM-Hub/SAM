"""Tests for C-Phase 4 (Workstream C8): Runtime Operational Intelligence.

Memverifikasi observer Runtime mengagregasi publikasi seluruh runtime
(Status Matrix / Dependency View / Lifecycle View / Health Matrix) secara
read-only, tanpa mengubah lifecycle, tanpa publish state baru, hanya agregasi
publication yang sudah tersedia di PublicationRegistry.
"""
from __future__ import annotations
import dataclasses
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.runtime_intelligence import (
    RuntimeDependency,
    RuntimeDependencyView,
    RuntimeHealthEntry,
    RuntimeHealthMatrix,
    RuntimeIntelligenceObserver,
    RuntimeLifecycleEntry,
    RuntimeLifecycleView,
    RuntimeStatusEntry,
    RuntimeStatusMatrix,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry_mixed() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="mission", health_state="healthy", readiness_level="operational",
        operational_state="ready", metric_count=5, timeline_events=8, has_metadata=True,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="approval", health_state="exceptional", readiness_level="operational",
        operational_state="running", metric_count=0, has_lifecycle=True,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="execution", health_state="degraded", readiness_level="operational",
        operational_state="degraded", metric_count=3, timeline_events=4, has_metadata=True,
    )))
    return reg


class TestRuntimeStatusMatrix:
    def test_status_matrix(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        mt = o.status_matrix()
        assert isinstance(mt, RuntimeStatusMatrix)
        assert mt.total_runtimes == 3
        assert all(isinstance(e, RuntimeStatusEntry) for e in mt.entries)

    def test_status_derived_counts(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        mt = o.status_matrix()
        # mission ready, approval running, execution degraded
        assert mt.ready_count >= 1
        assert mt.degraded_count >= 1
        assert mt.operational_count >= 2

    def test_as_dict(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        d = o.status_matrix().as_dict()
        assert "total_runtimes" in d
        assert "runtimes" in d


class TestRuntimeDependencyView:
    def test_dependency_lists_runtimes(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        dv = o.dependency_view()
        rts = {d.runtime_id for d in dv.dependencies}
        assert "mission" in rts and "execution" in rts and "approval" in rts

    def test_dependencies_of_execution(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        dv = o.dependency_view()
        assert "workflow" in dv.dependencies_of("execution")
        assert "policy" in dv.dependencies_of("execution")

    def test_dependency_entry_immutable(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        assert all(isinstance(d, RuntimeDependency) for d in o.dependency_view().dependencies)


class TestRuntimeLifecycleView:
    def test_lifecycle_view(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        lc = o.lifecycle_view()
        assert isinstance(lc, RuntimeLifecycleView)
        assert all(isinstance(e, RuntimeLifecycleEntry) for e in lc.entries)
        # approval has_lifecycle True
        entry = {e.runtime_id: e for e in lc.entries}["approval"]
        assert entry.has_lifecycle

    def test_metadata_flag(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        lc = o.lifecycle_view()
        entry = {e.runtime_id: e for e in lc.entries}["mission"]
        assert entry.has_metadata


class TestRuntimeHealthMatrix:
    def test_health_matrix(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        hl = o.health_matrix()
        assert isinstance(hl, RuntimeHealthMatrix)
        assert all(isinstance(e, RuntimeHealthEntry) for e in hl.entries)

    def test_health_aggregated(self):
        o = RuntimeIntelligenceObserver(_registry_mixed())
        hl = o.health_matrix()
        # ada degraded -> aggregated degraded
        assert hl.aggregated_health == "degraded"
        assert hl.degraded_count >= 1
        assert hl.unhealthy_count == hl.degraded_count + hl.critical_count


class TestRuntimeObserverReadOnly:
    def test_no_registry_mutation(self):
        """Read-only: memanggil observer TIDAK menambah/mengubah publikasi."""
        reg = PublicationRegistry()
        o = RuntimeIntelligenceObserver(reg)
        before = len(reg.observe_all().publications)
        o.status_matrix(); o.dependency_view(); o.lifecycle_view(); o.health_matrix()
        after = len(reg.observe_all().publications)
        assert before == after == 0
        assert reg.registered_runtimes() == frozenset()

    def test_dto_are_immutable(self):
        for cls in (RuntimeStatusEntry, RuntimeStatusMatrix,
                    RuntimeDependency, RuntimeDependencyView,
                    RuntimeLifecycleEntry, RuntimeLifecycleView,
                    RuntimeHealthEntry, RuntimeHealthMatrix):
            assert dataclasses.is_dataclass(cls)
            assert cls.__dataclass_params__.frozen


class TestRuntimeWiring:
    def test_wiring_getters_shortcuts(self):
        from sam.runtime_service.api.observation_wiring import (
            get_runtime_intelligence_observer,
            observe_runtimes,
            observe_runtime_dependencies,
            observe_runtime_lifecycle,
            observe_runtime_health,
        )
        assert isinstance(get_runtime_intelligence_observer(), RuntimeIntelligenceObserver)
        assert isinstance(observe_runtimes(), RuntimeStatusMatrix)
        assert isinstance(observe_runtime_dependencies(), RuntimeDependencyView)
        assert isinstance(observe_runtime_lifecycle(), RuntimeLifecycleView)
        assert isinstance(observe_runtime_health(), RuntimeHealthMatrix)
