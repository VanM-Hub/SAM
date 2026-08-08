"""Tests for C-Phase 2: Gap Resolution.

Tests all 6 gap resolvers: GAP-001 through GAP-006 + coordinator.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.gaps import (
    ApprovalHealthDetail,
    ApprovalHealthInspector,
    EventBusDescriptor,
    EventBusInspector,
    EventBusRegistry,
    GapResolutionCoordinator,
    GapResolutionReport,
    OperationalAnalytics,
    OperationalAnalyticsReport,
    OperationalTrend,
    PerRuntimeHealthDetail,
    PreviewAvailability,
    PreviewAvailabilityIndex,
    PreviewConsumerIndex,
    ReadinessDetail,
    ReadinessReport,
    ReadinessReporter,
    UnifiedHealthReport,
    UnifiedHealthReporter,
)


# ── Test Helpers ──

def _make_adapter(runtime_id: str, health="healthy", readiness="operational",
                  metrics=5, dashboards=3, health_checks=3, snapshots=5,
                  timeline=10, has_preview=True, has_metadata=True,
                  has_lifecycle=True, operational="running") -> PublicationAdapter:
    pub = RuntimePublication(
        runtime_id=runtime_id,
        health_state=health,
        readiness_level=readiness,
        operational_state=operational,
        metric_count=metrics,
        dashboard_count=dashboards,
        health_check_count=health_checks,
        snapshot_count=snapshots,
        timeline_events=timeline,
        has_preview=has_preview,
        has_metadata=has_metadata,
        has_lifecycle=has_lifecycle,
    )
    return _adapter_for(pub)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry_with(*adapters: PublicationAdapter) -> PublicationRegistry:
    reg = PublicationRegistry()
    for a in adapters:
        reg.register(a)
    return reg


# ═══════════════════════════════════════════════════════════════════════
# GAP-001: Unified Health Dashboard
# ═══════════════════════════════════════════════════════════════════════

class TestUnifiedHealthReporter:
    """GAP-001: Unified health report generation."""

    def test_empty_registry(self):
        reg = PublicationRegistry()
        reporter = UnifiedHealthReporter(reg)
        report = reporter.report()
        assert isinstance(report, UnifiedHealthReport)
        assert report.total_runtimes == 0
        assert report.status == "ok"

    def test_single_healthy_runtime(self):
        reg = _registry_with(_make_adapter("mission"))
        reporter = UnifiedHealthReporter(reg)
        report = reporter.report()
        assert report.total_runtimes == 1
        assert report.healthy_count == 1
        assert report.degraded_count == 0
        assert report.unhealthy_count == 0
        assert report.aggregated_health == "healthy"

    def test_single_unhealthy_runtime(self):
        reg = _registry_with(_make_adapter("mission", health="unhealthy"))
        report = UnifiedHealthReporter(reg).report()
        assert report.healthy_count == 0
        assert report.unhealthy_count == 1
        assert report.aggregated_health == "unhealthy"

    def test_single_degraded_runtime(self):
        reg = _registry_with(_make_adapter("policy", health="degraded"))
        report = UnifiedHealthReporter(reg).report()
        assert report.degraded_count == 1
        assert report.aggregated_health == "degraded"

    def test_mixed_health(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="degraded"),
            _make_adapter("artifact", health="unhealthy"),
            _make_adapter("approval", health="unknown"),
        )
        report = UnifiedHealthReporter(reg).report()
        assert report.total_runtimes == 4
        assert report.healthy_count == 1
        assert report.degraded_count == 1
        assert report.unhealthy_count == 1
        assert report.unknown_count == 1
        assert report.aggregated_health == "unhealthy"

    def test_per_runtime_details(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy", readiness="operational"),
            _make_adapter("policy", health="degraded", readiness="activated"),
        )
        report = UnifiedHealthReporter(reg).report()
        assert len(report.per_runtime) == 2
        detail_map = {d.runtime_id: d for d in report.per_runtime}
        assert detail_map["mission"].health_state == "healthy"
        assert detail_map["mission"].readiness_level == "operational"
        assert detail_map["policy"].health_state == "degraded"
        assert detail_map["policy"].has_preview is True

    def test_unhealthy_recommendation(self):
        reg = _registry_with(_make_adapter("workflow", health="unhealthy"))
        report = UnifiedHealthReporter(reg).report()
        assert len(report.recommendations) >= 1
        assert any("tidak sehat" in r for r in report.recommendations)

    def test_degraded_recommendation_with_missing_health_checker(self):
        reg = _registry_with(_make_adapter(
            "artifact", health="degraded", health_checks=0, metrics=0
        ))
        report = UnifiedHealthReporter(reg).report()
        assert len(report.recommendations) >= 1
        assert any("health checker" in r for r in report.recommendations)

    def test_unknown_recommendation(self):
        reg = _registry_with(_make_adapter("knowledge", health="unknown"))
        report = UnifiedHealthReporter(reg).report()
        assert len(report.recommendations) >= 1
        assert any("Health state tidak diketahui" in r for r in report.recommendations)

    def test_healthy_no_recommendation(self):
        reg = _registry_with(_make_adapter("memory", health="healthy"))
        report = UnifiedHealthReporter(reg).report()
        # healthy runtime with operational readiness → no recommendation
        mission_recommend = [r for r in report.recommendations if "memory" in r]
        assert len(mission_recommend) == 0

    def test_immutable_report(self):
        reg = _registry_with(_make_adapter("mission"))
        report = UnifiedHealthReporter(reg).report()
        with pytest.raises(Exception):
            report.healthy_count = 99  # type: ignore[misc]

    def test_as_dict_output(self):
        reg = _registry_with(
            _make_adapter("mission"),
            _make_adapter("policy"),
        )
        report = UnifiedHealthReporter(reg).report()
        d = report.as_dict()
        assert d["status"] == "ok"
        assert d["total_runtimes"] == 2
        assert len(d["per_runtime"]) == 2
        assert isinstance(d["recommendations"], list)


# ═══════════════════════════════════════════════════════════════════════
# GAP-002: Preview Consumer Wiring
# ═══════════════════════════════════════════════════════════════════════

class TestPreviewConsumerIndex:
    """GAP-002: Preview consumer availability mapping."""

    def test_empty_registry(self):
        reg = PublicationRegistry()
        idx = PreviewConsumerIndex(reg)
        result = idx.index()
        assert isinstance(result, PreviewAvailabilityIndex)
        assert result.total_preview_available == 0

    def test_with_preview_runtimes(self):
        reg = _registry_with(
            _make_adapter("mission", has_preview=True),
            _make_adapter("workflow", has_preview=True),
        )
        idx = PreviewConsumerIndex(reg)
        result = idx.index()
        assert result.total_preview_available == 2
        assert len(result.entries) == 2

    def test_without_preview_runtime(self):
        reg = _registry_with(
            _make_adapter("runtime_service", has_preview=False),
        )
        idx = PreviewConsumerIndex(reg)
        result = idx.index()
        assert result.total_preview_available == 0
        assert result.entries[0].consumer_status == "not_applicable"

    def test_infer_preview_type(self):
        assert PreviewConsumerIndex._infer_preview_type("mission") == "mission_preview"
        assert PreviewConsumerIndex._infer_preview_type("workflow") == "workflow_preview"
        assert PreviewConsumerIndex._infer_preview_type("unknown_runtime") == "unknown_runtime_preview"

    def test_consumer_wiring_check(self):
        # Known wired runtimes
        for rid in ("knowledge", "workflow", "mission", "audit", "execution"):
            consumers = PreviewConsumerIndex._check_consumer_wiring(rid)
            assert "observation_gateway" in consumers

    def test_immutable_index(self):
        reg = _registry_with(_make_adapter("mission"))
        idx = PreviewConsumerIndex(reg)
        result = idx.index()
        with pytest.raises(Exception):
            result.total_consumers_wired = 99  # type: ignore[misc]

    def test_as_dict(self):
        reg = _registry_with(
            _make_adapter("mission", has_preview=True),
            _make_adapter("approval", has_preview=True),
        )
        idx = PreviewConsumerIndex(reg)
        d = idx.index().as_dict()
        assert d["total_preview_available"] == 2
        assert len(d["entries"]) == 2


# ═══════════════════════════════════════════════════════════════════════
# GAP-003: Event Bus Consolidation
# ═══════════════════════════════════════════════════════════════════════

class TestEventBusInspector:
    """GAP-003: Event bus inspection."""

    def test_inspect_finds_three_buses(self):
        inspector = EventBusInspector()
        registry = inspector.inspect()
        assert isinstance(registry, EventBusRegistry)
        assert registry.total_buses == 3
        assert registry.consolidated is False

    def test_buses_are_immutable(self):
        inspector = EventBusInspector()
        registry = inspector.inspect()
        for bus in registry.buses:
            assert isinstance(bus, EventBusDescriptor)
            assert bus.location
            assert bus.event_class
            assert bus.handler_pattern in ("sync", "async", "both")

    def test_recommendation_present(self):
        inspector = EventBusInspector()
        registry = inspector.inspect()
        assert len(registry.recommendation) > 50
        assert "event class" in registry.recommendation.lower()

    def test_as_dict(self):
        inspector = EventBusInspector()
        d = inspector.inspect().as_dict()
        assert d["total_buses"] == 3
        assert d["consolidated"] is False
        assert len(d["buses"]) == 3
        assert "recommendation" in d


# ═══════════════════════════════════════════════════════════════════════
# GAP-004: Readiness Endpoint
# ═══════════════════════════════════════════════════════════════════════

class TestReadinessReporter:
    """GAP-004: Readiness report generation."""

    def test_empty_registry(self):
        reg = PublicationRegistry()
        reporter = ReadinessReporter(reg)
        report = reporter.report()
        assert isinstance(report, ReadinessReport)
        assert report.total_runtimes == 0
        assert report.platform_readiness == "planned"

    def test_all_operational(self):
        reg = _registry_with(
            _make_adapter("mission", readiness="operational"),
            _make_adapter("policy", readiness="operational"),
            _make_adapter("workflow", readiness="operational"),
        )
        report = ReadinessReporter(reg).report()
        assert report.operational_count == 3
        assert report.platform_readiness == "operational"

    def test_all_activated(self):
        reg = _registry_with(
            _make_adapter("mission", readiness="activated"),
            _make_adapter("policy", readiness="activated"),
        )
        report = ReadinessReporter(reg).report()
        assert report.activated_count == 2
        assert report.platform_readiness == "activated"

    def test_mixed_readiness(self):
        reg = _registry_with(
            _make_adapter("mission", readiness="operational"),
            _make_adapter("policy", readiness="activated"),
            _make_adapter("artifact", readiness="planned"),
            _make_adapter("approval", readiness="unknown"),
        )
        report = ReadinessReporter(reg).report()
        assert report.operational_count == 1
        assert report.activated_count == 1
        assert report.planned_count == 1
        assert report.unknown_count == 1
        assert report.platform_readiness == "planned"

    def test_gaps_for_non_operational(self):
        reg = _registry_with(
            _make_adapter("mission", readiness="operational"),
            _make_adapter("artifact", readiness="planned"),
        )
        report = ReadinessReporter(reg).report()
        assert len(report.gaps) > 0
        assert any("planned" in g for g in report.gaps)

    def test_per_runtime_activation_status(self):
        reg = _registry_with(_make_adapter("mission", readiness="operational"))
        report = ReadinessReporter(reg).report()
        detail = report.per_runtime[0]
        assert detail.activation_status in ("activated", "pending", "deferred")
        assert detail.in_baseline_ci is True  # mission is in baseline

    def test_immutable_report(self):
        reg = _registry_with(_make_adapter("mission"))
        report = ReadinessReporter(reg).report()
        with pytest.raises(Exception):
            report.platform_readiness = "changed"  # type: ignore[misc]

    def test_as_dict(self):
        reg = _registry_with(
            _make_adapter("mission", readiness="operational"),
            _make_adapter("policy", readiness="activated"),
        )
        d = ReadinessReporter(reg).report().as_dict()
        assert d["total_runtimes"] == 2
        assert d["platform_readiness"] in ("operational", "activated", "planned")
        assert len(d["per_runtime"]) == 2


# ═══════════════════════════════════════════════════════════════════════
# GAP-005: Analytics Engine
# ═══════════════════════════════════════════════════════════════════════

class TestOperationalAnalytics:
    """GAP-005: Analytics report generation."""

    def test_empty_registry(self):
        reg = PublicationRegistry()
        analytics = OperationalAnalytics(reg)
        report = analytics.analyze()
        assert isinstance(report, OperationalAnalyticsReport)
        assert report.total_runtimes == 0

    def test_metric_density_high(self):
        reg = _registry_with(_make_adapter("mission", metrics=10))
        report = OperationalAnalytics(reg).analyze()
        trend = report.per_runtime_trend[0]
        assert trend.metric_density == "high"
        assert trend.runtime_id == "mission"

    def test_metric_density_medium(self):
        reg = _registry_with(_make_adapter("policy", metrics=3))
        report = OperationalAnalytics(reg).analyze()
        assert report.per_runtime_trend[0].metric_density == "medium"

    def test_metric_density_low(self):
        reg = _registry_with(_make_adapter("artifact", metrics=0))
        report = OperationalAnalytics(reg).analyze()
        assert report.per_runtime_trend[0].metric_density == "low"

    def test_dashboard_coverage_full(self):
        reg = _registry_with(_make_adapter("mission", dashboards=5))
        report = OperationalAnalytics(reg).analyze()
        assert report.per_runtime_trend[0].dashboard_coverage == "full"

    def test_dashboard_coverage_partial(self):
        reg = _registry_with(_make_adapter("policy", dashboards=2))
        report = OperationalAnalytics(reg).analyze()
        assert report.per_runtime_trend[0].dashboard_coverage == "partial"

    def test_dashboard_coverage_none(self):
        reg = _registry_with(_make_adapter("artifact", dashboards=0))
        report = OperationalAnalytics(reg).analyze()
        assert report.per_runtime_trend[0].dashboard_coverage == "none"

    def test_health_distribution(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="healthy"),
            _make_adapter("artifact", health="degraded"),
        )
        report = OperationalAnalytics(reg).analyze()
        assert report.health_distribution["healthy"] == 2
        assert report.health_distribution["degraded"] == 1
        assert report.health_distribution["unhealthy"] == 0

    def test_insights_for_unhealthy(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="unhealthy"),
        )
        report = OperationalAnalytics(reg).analyze()
        assert len(report.insights) > 0
        assert any("unhealthy" in i.lower() for i in report.insights)

    def test_insights_for_low_metrics(self):
        reg = _registry_with(
            _make_adapter("mission", metrics=0),
            _make_adapter("policy", metrics=0),
            _make_adapter("artifact", metrics=0),
            _make_adapter("audit", metrics=0),
        )
        report = OperationalAnalytics(reg).analyze()
        assert any("metric" in i.lower() for i in report.insights)

    def test_overall_density_calculation(self):
        reg = _registry_with(
            _make_adapter("mission", metrics=10),
            _make_adapter("policy", metrics=10),
            _make_adapter("artifact", metrics=10),
        )
        report = OperationalAnalytics(reg).analyze()
        assert report.overall_metric_density == "high"

    def test_immutable_report(self):
        reg = _registry_with(_make_adapter("mission"))
        report = OperationalAnalytics(reg).analyze()
        with pytest.raises(Exception):
            report.overall_metric_density = "changed"  # type: ignore[misc]

    def test_as_dict(self):
        reg = _registry_with(
            _make_adapter("mission", metrics=10),
            _make_adapter("policy", metrics=3),
        )
        d = OperationalAnalytics(reg).analyze().as_dict()
        assert d["total_runtimes"] == 2
        assert len(d["per_runtime_trend"]) == 2
        assert isinstance(d["health_distribution"], dict)


# ═══════════════════════════════════════════════════════════════════════
# GAP-006: Approval Self-Reporting
# ═══════════════════════════════════════════════════════════════════════

class TestApprovalHealthInspector:
    """GAP-006: Approval health self-report assessment."""

    def test_inspect_returns_detail(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        assert isinstance(detail, ApprovalHealthDetail)
        assert detail.runtime_id == "approval"

    def test_approval_has_analytics(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        assert detail.analytics_available is True
        assert detail.conversation_analytics is True
        assert detail.dashboard_analytics is True

    def test_approval_no_health_checker(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        assert detail.has_health_checker is False
        assert detail.has_monitor is False
        assert detail.is_self_reporting is False

    def test_has_recommendation(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        assert len(detail.recommendation) > 20
        assert "health" in detail.recommendation.lower()

    def test_engine_files_count(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        assert detail.engine_files >= 40  # approval is 48-file engine

    def test_immutable(self):
        inspector = ApprovalHealthInspector()
        detail = inspector.inspect()
        with pytest.raises(Exception):
            detail.is_self_reporting = True  # type: ignore[misc]

    def test_as_dict(self):
        inspector = ApprovalHealthInspector()
        d = inspector.inspect().as_dict()
        assert d["runtime_id"] == "approval"
        assert isinstance(d["engine_files"], int)
        assert isinstance(d["is_self_reporting"], bool)


# ═══════════════════════════════════════════════════════════════════════
# GAP Resolution Coordinator
# ═══════════════════════════════════════════════════════════════════════

class TestGapResolutionCoordinator:
    """Integration: coordinator aggregates all 6 gap resolutions."""

    def test_full_registry_resolve_all(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy", readiness="operational"),
            _make_adapter("workflow", health="healthy", readiness="activated"),
            _make_adapter("policy", health="healthy", readiness="activated"),
            _make_adapter("execution", health="healthy", readiness="activated"),
            _make_adapter("approval", health="healthy", readiness="operational"),
            _make_adapter("audit", health="healthy", readiness="activated"),
            _make_adapter("knowledge", health="healthy", readiness="operational"),
            _make_adapter("memory", health="healthy", readiness="operational"),
            _make_adapter("artifact", health="degraded", readiness="activated"),
            _make_adapter("runtime_service", health="healthy", readiness="operational"),
        )
        coordinator = GapResolutionCoordinator(reg)
        report = coordinator.resolve_all()

        assert isinstance(report, GapResolutionReport)
        assert report.total_gaps == 6
        assert report.resolved_gaps == 6
        assert isinstance(report.unified_health, UnifiedHealthReport)
        assert isinstance(report.preview_index, PreviewAvailabilityIndex)
        assert isinstance(report.event_bus_registry, EventBusRegistry)
        assert isinstance(report.readiness, ReadinessReport)
        assert isinstance(report.analytics, OperationalAnalyticsReport)
        assert isinstance(report.approval_health, ApprovalHealthDetail)

    def test_resolve_all_healthy_registry(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="healthy"),
        )
        coordinator = GapResolutionCoordinator(reg)
        report = coordinator.resolve_all()
        assert report.unified_health.aggregated_health == "healthy"

    def test_resolve_all_unhealthy_registry(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="unhealthy"),
        )
        report = GapResolutionCoordinator(reg).resolve_all()
        assert report.unified_health.aggregated_health == "unhealthy"
        assert report.unified_health.unhealthy_count == 1

    def test_resolve_all_degraded_mixed(self):
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("artifact", health="degraded"),
        )
        report = GapResolutionCoordinator(reg).resolve_all()
        assert "degraded" in report.summary()

    def test_summary_string(self):
        reg = _registry_with(_make_adapter("mission"))
        report = GapResolutionCoordinator(reg).resolve_all()
        summary = report.summary()
        assert "Gap Resolution" in summary
        assert "6/6" in summary
        assert isinstance(summary, str)
        assert len(summary) > 20

    def test_empty_registry(self):
        reg = PublicationRegistry()
        coordinator = GapResolutionCoordinator(reg)
        report = coordinator.resolve_all()

        assert report.unified_health.total_runtimes == 0
        assert report.readiness.total_runtimes == 0
        assert report.analytics.total_runtimes == 0
        # Event bus + approval exist regardless of registry
        assert report.event_bus_registry.total_buses == 3
        assert report.approval_health.engine_files >= 40

    def test_coordinator_immutable(self):
        reg = _registry_with(_make_adapter("mission"))
        report = GapResolutionCoordinator(reg).resolve_all()
        with pytest.raises(Exception):
            report.resolved_gaps = 0  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════
# Cross-Gap Integration
# ═══════════════════════════════════════════════════════════════════════

class TestCrossGapIntegration:
    """Integration: cross-cutting scenarios across multiple gaps."""

    def test_all_gaps_consume_same_registry(self):
        """All resolvers read from the same registry (read-only consistency)."""
        reg = _registry_with(
            _make_adapter("mission", health="healthy", readiness="operational"),
            _make_adapter("policy", health="degraded", readiness="activated"),
        )
        health = UnifiedHealthReporter(reg).report()
        readiness = ReadinessReporter(reg).report()
        analytics = OperationalAnalytics(reg).analyze()

        assert health.total_runtimes == readiness.total_runtimes == analytics.total_runtimes

    def test_health_analytics_consistency(self):
        """Health distribution in analytics matches health report."""
        reg = _registry_with(
            _make_adapter("mission", health="healthy"),
            _make_adapter("policy", health="degraded"),
            _make_adapter("artifact", health="unhealthy"),
        )
        health = UnifiedHealthReporter(reg).report()
        analytics = OperationalAnalytics(reg).analyze()

        assert analytics.health_distribution["healthy"] == health.healthy_count
        assert analytics.health_distribution["degraded"] == health.degraded_count
        assert analytics.health_distribution["unhealthy"] == health.unhealthy_count

    def test_readiness_gap_detection(self):
        """Non-operational runtimes generate readiness gaps."""
        reg = _registry_with(
            _make_adapter("mission", readiness="operational"),
            _make_adapter("artifact", readiness="planned"),
        )
        report = ReadinessReporter(reg).report()
        assert len(report.gaps) > 0
        # Operational runtime should not have gaps
        mission_gaps = [g for g in report.gaps if "mission" in g and "preview tidak tersedia" not in g.lower()]
        assert len(mission_gaps) == 0
        # Planned (non-operational) should have gap
        assert any("planned" in g for g in report.gaps)
