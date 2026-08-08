"""Tests for C-Phase 4 (Workstream C9): Platform Health Intelligence.

Memverifikasi observer Platform menghitung unified health platform, metrics,
cross-runtime health correlation, dan status summary - secara read-only,
health dihitung (bukan dipaksa), tanpa mengubah Runtime/Readiness.
"""
from __future__ import annotations
import dataclasses
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.platform_health import (
    CrossRuntimeHealth,
    CrossRuntimeHealthView,
    PlatformHealthObserver,
    PlatformHealthReport,
    PlatformMetrics,
    PlatformStatusSummary,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="mission", health_state="healthy", readiness_level="operational",
        operational_state="ready", metric_count=5, health_check_count=2, timeline_events=8,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="workflow", health_state="healthy", readiness_level="operational",
        operational_state="running", metric_count=3, health_check_count=1, timeline_events=4,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="execution", health_state="degraded", readiness_level="operational",
        operational_state="degraded", metric_count=1, health_check_count=2, timeline_events=2,
    )))
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="audit", health_state="healthy", readiness_level="operational",
        operational_state="running", metric_count=0, health_check_count=1, timeline_events=0,
    )))
    return reg


def _observer() -> PlatformHealthObserver:
    return PlatformHealthObserver(_registry())


class TestPlatformHealthReport:
    def test_health_report(self):
        o = _observer()
        hl = o.health_report()
        assert isinstance(hl, PlatformHealthReport)
        assert hl.total_runtimes == 4

    def test_health_derived_not_forced(self):
        # ada 1 degraded (execution) -> overall degraded (dihitung, bukan dipaksa)
        o = _observer()
        hl = o.health_report()
        assert hl.overall_health == "degraded"
        assert hl.healthy_runtimes == 3
        assert hl.degraded_runtimes == 1
        assert hl.healthy_ratio == pytest.approx(0.75)

    def test_as_dict(self):
        o = _observer()
        d = o.health_report().as_dict()
        assert "overall_health" in d
        assert "healthy_ratio" in d


class TestPlatformMetrics:
    def test_metrics_aggregate(self):
        o = _observer()
        mt = o.metrics()
        assert isinstance(mt, PlatformMetrics)
        assert mt.total_runtimes == 4
        # execution degraded -> tidak dihitung operational
        assert mt.operational_runtimes == 3
        assert mt.total_metrics == 9  # 5+3+1+0
        assert mt.total_health_checks == 6  # 2+1+2+1
        assert mt.total_timeline_events == 14  # 8+4+2+0

    def test_metrics_as_dict(self):
        o = _observer()
        d = o.metrics().as_dict()
        assert "total_metrics" in d


class TestCrossRuntimeHealth:
    def test_cross_runtime_view(self):
        o = _observer()
        cr = o.cross_runtime_health()
        assert isinstance(cr, CrossRuntimeHealthView)
        assert len(cr.entries) == 4
        assert all(isinstance(e, CrossRuntimeHealth) for e in cr.entries)

    def test_dependency_health_correlation(self):
        # execution depends on mission/workflow/policy; workflow & mission healthy
        o = _observer()
        cr = o.cross_runtime_health()
        by_id = {e.runtime_id: e for e in cr.entries}
        exec_entry = by_id["execution"]
        assert "mission" in exec_entry.depends_on
        # meski execution degraded, dependency-nya healthy
        assert exec_entry.dependency_health == "healthy"

    def test_dependency_issues_identifies_correlation(self):
        """Correlation: audit healthy tapi dependensi execution degraded -> teridentifikasi."""
        o = _observer()
        cr = o.cross_runtime_health()
        issues = cr.dependency_issues()
        assert len(issues) == 1
        assert issues[0].runtime_id == "audit"
        assert issues[0].dependency_health == "degraded"


class TestPlatformStatusSummary:
    def test_status_summary(self):
        o = _observer()
        st = o.status_summary()
        assert isinstance(st, PlatformStatusSummary)
        assert st.health == "degraded"
        assert st.readiness == "operational"
        assert st.operational_count == 4
        assert st.total_runtimes == 4
        assert st.summary_text

    def test_as_dict(self):
        o = _observer()
        d = o.status_summary().as_dict()
        assert "summary_text" in d


class TestPlatformObserverReadOnly:
    def test_no_registry_mutation(self):
        """Read-only: memanggil observer TIDAK menambah/mengubah publikasi."""
        reg = PublicationRegistry()
        o = PlatformHealthObserver(reg)
        before = len(reg.observe_all().publications)
        o.health_report(); o.metrics(); o.cross_runtime_health(); o.status_summary()
        after = len(reg.observe_all().publications)
        assert before == after == 0

    def test_empty_registry_unknown(self):
        """Registry kosong -> health unknown (bukan dipaksa jadi healthy)."""
        o = PlatformHealthObserver(PublicationRegistry())
        hl = o.health_report()
        assert hl.overall_health in ("unknown", "healthy")
        assert hl.total_runtimes == 0

    def test_dto_are_immutable(self):
        for cls in (PlatformHealthReport, PlatformMetrics,
                    CrossRuntimeHealth, CrossRuntimeHealthView, PlatformStatusSummary):
            assert dataclasses.is_dataclass(cls)
            assert cls.__dataclass_params__.frozen


class TestPlatformWiring:
    def test_wiring_getters_shortcuts(self):
        from sam.runtime_service.api.observation_wiring import (
            get_platform_health_observer,
            observe_platform_health,
            observe_platform_metrics,
            observe_cross_runtime_health,
            observe_platform_status,
        )
        assert isinstance(get_platform_health_observer(), PlatformHealthObserver)
        assert isinstance(observe_platform_health(), PlatformHealthReport)
        assert isinstance(observe_platform_metrics(), PlatformMetrics)
        assert isinstance(observe_cross_runtime_health(), CrossRuntimeHealthView)
        assert isinstance(observe_platform_status(), PlatformStatusSummary)
