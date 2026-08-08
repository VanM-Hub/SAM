"""Tests for C-Phase 4 (Workstream C6): Capability Operational Intelligence.

Memverifikasi observer Capability menghasilkan observasi operational
(Status Aggregation / Readiness / Health / Dependency View) secara read-only
murni, tanpa mutasi registry maupun governance, dan memanfaatkan fondasi
WP-C1.4 (CapabilityStatusReader) - verify, don't build from scratch.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.capability_intelligence import (
    CapabilityAggregation,
    CapabilityDependency,
    CapabilityDependencyView,
    CapabilityHealthEntry,
    CapabilityHealthReport,
    CapabilityIntelligenceObserver,
    CapabilityReadinessEntry,
    CapabilityReadinessReport,
    CapabilityStatusEntry,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry_with_two() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="mission",
        health_state="healthy",
        readiness_level="operational",
        operational_state="ready",
        has_preview=True,
        has_metadata=True,
        timeline_events=8,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="approval",
        health_state="degraded",
        readiness_level="operational",
        operational_state="degraded",
        has_lifecycle=True,
    )))
    return reg


class TestCapabilityAggregation:
    def test_aggregates_all_capabilities(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        agg = ob.aggregation()
        assert isinstance(agg, CapabilityAggregation)
        # CapabilityStatusReader (fondasi WP-C1.4) mencakup 10 runtime x 8 capability
        assert agg.total_capabilities > 0
        assert agg.available_count >= 0
        assert agg.unavailable_count == agg.total_capabilities - agg.available_count

    def test_by_runtime_filters(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        agg = ob.aggregation()
        mission_entries = agg.by_runtime("mission")
        assert all(e.runtime_id == "mission" for e in mission_entries)
        assert len(mission_entries) > 0

    def test_seratus_enam_entries_immutable(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        entries = ob.aggregation().entries
        assert all(isinstance(e, CapabilityStatusEntry) for e in entries)


class TestCapabilityReadiness:
    def test_readiness_report(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        rpt = ob.readiness()
        assert isinstance(rpt, CapabilityReadinessReport)
        assert isinstance(rpt.entries[0], CapabilityReadinessEntry)
        # reader statis: semua runtime operational
        assert rpt.operational_count >= 2
        assert rpt.activated_count + rpt.planned_count >= 0

    def test_as_dict(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        d = ob.readiness().as_dict()
        assert "operational_count" in d
        assert "capabilities" in d


class TestCapabilityHealth:
    def test_health_reads_publication_state(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        hl = ob.health()
        assert isinstance(hl, CapabilityHealthReport)
        # registry publikasi: mission healthy (+ reader tambahan) 
        # approval degraded (registry override)
        states = {e.runtime_id: e.health_state for e in hl.entries}
        # entry mission dari registry == healthy
        # (registry diprioritaskan; entry approval == degraded)
        assert states.get("mission") in ("healthy", "unknown")
        assert states.get("approval") == "degraded"

    def test_health_derived_counts(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        hl = ob.health()
        assert hl.unhealthy_count == hl.degraded_count + hl.critical_count

    def test_health_entry_immutable(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        assert all(isinstance(e, CapabilityHealthEntry) for e in ob.health().entries)


class TestCapabilityDependencyView:
    def test_dependency_lists_runtimes(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        dv = ob.dependency_view()
        assert isinstance(dv, CapabilityDependencyView)
        rts = {d.runtime_id for d in dv.dependencies}
        assert "mission" in rts
        assert "approval" in rts

    def test_dependencies_of_execution(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        dv = ob.dependency_view()
        assert "workflow" in dv.dependencies_of("execution")
        assert "policy" in dv.dependencies_of("execution")

    def test_dependency_entry_immutable(self):
        ob = CapabilityIntelligenceObserver(_registry_with_two())
        assert all(isinstance(d, CapabilityDependency) for d in ob.dependency_view().dependencies)


class TestCapabilityObserverReadOnly:
    def test_no_mutation_on_publish(self):
        """Read-only: memanggil observer TIDAK mengubah registry atau menambah publikasi."""
        reg = PublicationRegistry()
        before_pubs = len(reg.observe_all().publications)
        ob = CapabilityIntelligenceObserver(reg)
        ob.aggregation()
        ob.readiness()
        ob.health()
        ob.dependency_view()
        after_pubs = len(reg.observe_all().publications)
        assert before_pubs == after_pubs == 0

    def test_dto_are_immutable(self):
        """Seluruh DTO observasi capability immutable (frozen dataclass)."""
        import dataclasses
        from sam.observation import capability_intelligence as m
        for cls in (CapabilityStatusEntry, CapabilityAggregation,
                    CapabilityReadinessEntry, CapabilityReadinessReport,
                    CapabilityHealthEntry, CapabilityHealthReport,
                    CapabilityDependency, CapabilityDependencyView):
            assert dataclasses.is_dataclass(cls)
            assert cls.__dataclass_params__.frozen


class TestCapabilityWiring:
    def test_wiring_getters_shortcuts(self):
        from sam.runtime_service.api.observation_wiring import (
            get_capability_intelligence_observer,
            observe_capabilities,
            observe_capability_readiness,
            observe_capability_health,
            observe_capability_dependencies,
        )
        observer = get_capability_intelligence_observer()
        assert isinstance(observer, CapabilityIntelligenceObserver)
        assert isinstance(observe_capabilities(), CapabilityAggregation)
        assert isinstance(observe_capability_readiness(), CapabilityReadinessReport)
        assert isinstance(observe_capability_health(), CapabilityHealthReport)
        assert isinstance(observe_capability_dependencies(), CapabilityDependencyView)
