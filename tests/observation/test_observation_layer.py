"""Tests: Observation Layer — C-Phase 1 Integration.

WP-C1.1: publication adapter & registry tests
WP-C1.2: timeline aggregation tests
WP-C1.3: health integration tests
WP-C1.4: capability status tests
WP-C1.5: evidence integration tests
WP-C1.6: consumer integration tests

Semua test bersifat READ-ONLY — tidak mengubah runtime state.
"""
from __future__ import annotations

import pytest

from sam.observation.adapters import (
    ApprovalPublicationAdapter,
    ArtifactPublicationAdapter,
    AuditPublicationAdapter,
    ExecutionPublicationAdapter,
    KnowledgePublicationAdapter,
    MemoryPublicationAdapter,
    MissionPublicationAdapter,
    PolicyPublicationAdapter,
    RuntimeServicePublicationAdapter,
    WorkflowPublicationAdapter,
)
from sam.observation.capability import CapabilityStatusReader, CapabilityMatrix, CapabilityStatus
from sam.observation.evidence import EvidenceEntry, EvidenceExplorer, EvidenceIndex
from sam.observation.publication import (
    ObservationReport,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.timeline import (
    TimelineAggregator,
    TimelineEvent,
    TimelineView,
)
from sam.runtime_service.api.observation_endpoint import (
    HealthOverviewResponse,
    ObservationGateway,
    ObservationResponse,
)
from sam.runtime_service.api.observation_wiring import (
    create_publication_registry,
    get_observation_gateway,
    get_publication_registry,
)


# ═══════════════════════════════════════════════════════════
# WP-C1.1: Publication Adapter & Registry
# ═══════════════════════════════════════════════════════════

class TestPublicationDTO:
    """RuntimePublication DTO — immutable, as_dict."""

    def test_create_publication(self):
        p = RuntimePublication(runtime_id="test")
        assert p.runtime_id == "test"
        assert p.health_state == "unknown"
        assert p.readiness_level == "unknown"

    def test_as_dict(self):
        p = RuntimePublication(runtime_id="test", health_state="healthy",
                              readiness_level="operational")
        d = p.as_dict()
        assert d["runtime_id"] == "test"
        assert d["health_state"] == "healthy"
        assert d["readiness_level"] == "operational"


class TestObservationReport:
    """ObservationReport DTO — aggregate."""

    def test_create_empty(self):
        r = ObservationReport(runtime_count=0, publications=())
        assert r.runtime_count == 0
        assert r.aggregated_health == "unknown"

    def test_aggregated_healthy(self):
        p = RuntimePublication(runtime_id="a", health_state="healthy")
        r = ObservationReport(runtime_count=1, publications=(p,),
                              aggregated_health="healthy")
        assert r.aggregated_health == "healthy"

    def test_as_dict(self):
        p = RuntimePublication(runtime_id="a")
        r = ObservationReport(runtime_count=1, publications=(p,),
                              aggregated_health="healthy")
        d = r.as_dict()
        assert "publications" in d
        assert len(d["publications"]) == 1


class TestPublicationRegistry:
    """PublicationRegistry — register, observe, observe_all."""

    def test_register_and_observe(self):
        reg = PublicationRegistry()
        reg.register(MissionPublicationAdapter())
        assert "mission" in reg.registered_runtimes()

        pub = reg.observe("mission")
        assert pub is not None
        assert pub.runtime_id == "mission"
        assert pub.has_preview is True

    def test_observe_nonexistent(self):
        reg = PublicationRegistry()
        assert reg.observe("nonexistent") is None

    def test_observe_all(self):
        reg = PublicationRegistry()
        reg.register(MissionPublicationAdapter())
        reg.register(WorkflowPublicationAdapter())

        report = reg.observe_all()
        assert report.runtime_count == 2
        assert report.aggregated_health in ("healthy", "degraded", "unhealthy", "unknown")

    def test_full_registry_wiring(self):
        """Verify all 10 adapters register successfully."""
        reg = create_publication_registry()
        runtimes = reg.registered_runtimes()
        expected = {"mission", "workflow", "policy", "execution", "approval",
                     "audit", "knowledge", "memory", "artifact", "runtime_service"}
        assert runtimes == expected

        report = reg.observe_all()
        assert report.runtime_count == 10
        for p in report.publications:
            assert p.health_state in ("healthy", "degraded", "unhealthy", "unknown")
            assert p.readiness_level in ("operational", "activated", "planned", "unknown")


class TestAllAdapters:
    """Every adapter must conform to PublicationAdapter interface."""

    ADAPTERS = [
        MissionPublicationAdapter, WorkflowPublicationAdapter,
        PolicyPublicationAdapter, ExecutionPublicationAdapter,
        AuditPublicationAdapter, KnowledgePublicationAdapter,
        MemoryPublicationAdapter, ArtifactPublicationAdapter,
        ApprovalPublicationAdapter, RuntimeServicePublicationAdapter,
    ]

    @pytest.mark.parametrize("adapter_cls", ADAPTERS)
    def test_adapter_has_runtime_id(self, adapter_cls):
        adapter = adapter_cls()
        rid = adapter.runtime_id()
        assert isinstance(rid, str)
        assert len(rid) > 0

    @pytest.mark.parametrize("adapter_cls", ADAPTERS)
    def test_adapter_observe_returns_publication(self, adapter_cls):
        adapter = adapter_cls()
        pub = adapter.observe()
        assert isinstance(pub, RuntimePublication)
        assert pub.runtime_id == adapter.runtime_id()
        assert isinstance(pub.as_dict(), dict)

    @pytest.mark.parametrize("adapter_cls", ADAPTERS)
    def test_adapter_health_state(self, adapter_cls):
        adapter = adapter_cls()
        state = adapter.health_state()
        assert state in ("healthy", "degraded", "unhealthy", "unknown")


# ═══════════════════════════════════════════════════════════
# WP-C1.2: Timeline Integration
# ═══════════════════════════════════════════════════════════

class TestTimelineEvent:
    """TimelineEvent — immutable DTO."""

    def test_create(self):
        e = TimelineEvent(event_id="e1", source="mission", description="test")
        assert e.event_id == "e1"
        assert e.source == "mission"

    def test_as_dict(self):
        e = TimelineEvent(event_id="e1", source="mission",
                         description="test", order=1)
        d = e.as_dict()
        assert d["event_id"] == "e1"
        assert d["source"] == "mission"
        assert d["order"] == 1


class TestTimelineAggregator:
    """TimelineAggregator — collect, view, ordering."""

    def test_collect_single_source(self):
        agg = TimelineAggregator()
        agg.collect_from_mission()
        view = agg.view()
        assert view.total_events == 1
        assert view.sources_covered == ("mission",)

    def test_collect_all(self):
        agg = TimelineAggregator()
        agg.collect_all()
        view = agg.view()
        assert view.total_events == 4
        assert set(view.sources_covered) == {"mission", "execution", "approval", "audit"}

    def test_ordering_maintained(self):
        agg = TimelineAggregator()
        agg.collect_all()
        view = agg.view()
        for i in range(len(view.events) - 1):
            assert view.events[i].order <= view.events[i + 1].order


class TestTimelineView:
    """TimelineView — unified view."""

    def test_empty_view(self):
        v = TimelineView()
        assert v.total_events == 0
        assert v.sources_covered == ()

    def test_as_dict(self):
        agg = TimelineAggregator()
        agg.collect_all()
        v = agg.view()
        d = v.as_dict()
        assert d["total_events"] == 4
        assert len(d["events"]) == 4
        assert len(d["sources_covered"]) == 4


# ═══════════════════════════════════════════════════════════
# WP-C1.3: Health Integration
# ═══════════════════════════════════════════════════════════

class TestObservationGateway:
    """ObservationGateway — observe, observe_all, health_overview."""

    def test_observe_single_runtime(self):
        gw = get_observation_gateway()
        resp = gw.observe("mission")
        assert resp.status == "ok"
        assert resp.runtime_count == 1
        assert len(resp.publications) == 1

    def test_observe_nonexistent(self):
        gw = get_observation_gateway()
        resp = gw.observe("nonexistent")
        assert resp.status == "not_found"

    def test_observe_all(self):
        gw = get_observation_gateway()
        resp = gw.observe_all()
        assert resp.status == "ok"
        assert resp.runtime_count == 10
        assert resp.aggregated_health in ("healthy", "degraded", "unhealthy", "unknown")

    def test_health_overview(self):
        gw = get_observation_gateway()
        overview = gw.health_overview()
        assert overview.status == "ok"
        assert overview.healthy_count + overview.degraded_count + overview.unhealthy_count + overview.unknown_count == 10
        assert len(overview.per_runtime) == 10
        for rt in ("mission", "workflow", "policy", "execution", "approval",
                    "audit", "knowledge", "memory", "artifact", "runtime_service"):
            assert rt in overview.per_runtime

    def test_registered_runtimes(self):
        gw = get_observation_gateway()
        runtimes = gw.registered_runtimes()
        assert len(runtimes) == 10


class TestHealthOverviewResponse:
    """HealthOverviewResponse — DTO."""

    def test_healthy_overview(self):
        resp = HealthOverviewResponse(
            aggregated_health="healthy",
            healthy_count=8, degraded_count=0, unhealthy_count=0, unknown_count=2,
            per_runtime={"mission": "healthy"},
        )
        d = resp.as_dict()
        assert d["aggregated_health"] == "healthy"
        assert d["healthy_count"] == 8

    def test_degraded_overview(self):
        resp = HealthOverviewResponse(
            aggregated_health="degraded",
            healthy_count=6, degraded_count=2, unhealthy_count=0, unknown_count=2,
        )
        d = resp.as_dict()
        assert d["aggregated_health"] == "degraded"
        assert d["degraded_count"] == 2


# ═══════════════════════════════════════════════════════════
# WP-C1.4: Capability Status
# ═══════════════════════════════════════════════════════════

class TestCapabilityStatus:
    """CapabilityStatus — per-runtime capability."""

    def test_create(self):
        cs = CapabilityStatus(runtime_id="mission", readiness="operational",
                              has_dashboard=True, has_health=True, has_metrics=True)
        assert cs.runtime_id == "mission"
        assert cs.readiness == "operational"
        assert cs.capability_count() == 3

    def test_full_capability(self):
        cs = CapabilityStatus(
            runtime_id="full",
            has_dashboard=True, has_health=True, has_metrics=True,
            has_preview=True, has_timeline=True, has_lifecycle=True,
            has_metadata=True, has_snapshot=True,
        )
        assert cs.capability_count() == 8

    def test_as_dict(self):
        cs = CapabilityStatus(runtime_id="test", readiness="operational",
                              has_dashboard=True, has_health=True)
        d = cs.as_dict()
        assert d["runtime_id"] == "test"
        assert d["capabilities"]["dashboard"] is True
        assert d["capabilities"]["health"] is True


class TestCapabilityStatusReader:
    """CapabilityStatusReader — read all capability statuses."""

    def test_read_all(self):
        reader = CapabilityStatusReader()
        matrix = reader.read_all()
        assert matrix.total_runtime == 10
        assert matrix.operational_count == 10
        assert len(matrix.statuses) == 10

    def test_each_runtime_has_capabilities(self):
        reader = CapabilityStatusReader()
        matrix = reader.read_all()
        for cs in matrix.statuses:
            assert cs.capability_count() >= 2  # setiap runtime minimal dashboard+metadata
            assert cs.availability == "available"

    def test_capability_matrix_as_dict(self):
        reader = CapabilityStatusReader()
        matrix = reader.read_all()
        d = matrix.as_dict()
        assert d["total_runtime"] == 10
        assert len(d["statuses"]) == 10


# ═══════════════════════════════════════════════════════════
# WP-C1.5: Evidence Integration
# ═══════════════════════════════════════════════════════════

class TestEvidenceEntry:
    """EvidenceEntry — immutable DTO."""

    def test_create(self):
        e = EvidenceEntry(evidence_id="EV-001", source_runtime="mission",
                         category="inventory", verified=True)
        assert e.evidence_id == "EV-001"
        assert e.verified is True

    def test_as_dict(self):
        e = EvidenceEntry(evidence_id="EV-001", source_runtime="mission",
                         category="inventory", description="test")
        d = e.as_dict()
        assert d["evidence_id"] == "EV-001"
        assert d["category"] == "inventory"


class TestEvidenceExplorer:
    """EvidenceExplorer — index, filter, navigation."""

    def test_index_all(self):
        explorer = EvidenceExplorer()
        index = explorer.index_all()
        assert index.total_entries == 10
        assert index.verified_count == 10
        assert index.traceable_count == 10
        assert len(index.categories_covered) >= 3  # inventory, endpoint, publication, consumer

    def test_by_category(self):
        explorer = EvidenceExplorer()
        entries = explorer.by_category("inventory")
        assert len(entries) == 4  # EV-C1-01 through EV-C1-04
        for e in entries:
            assert e.category == "inventory"

    def test_by_runtime(self):
        explorer = EvidenceExplorer()
        entries = explorer.by_runtime("mission")
        assert len(entries) >= 1
        for e in entries:
            assert e.source_runtime == "mission"

    def test_by_nonexistent_category(self):
        explorer = EvidenceExplorer()
        entries = explorer.by_category("nonexistent")
        assert entries == []

    def test_by_nonexistent_runtime(self):
        explorer = EvidenceExplorer()
        entries = explorer.by_runtime("nonexistent")
        assert entries == []


class TestEvidenceIndex:
    """EvidenceIndex — immutable aggregate."""

    def test_empty_index(self):
        idx = EvidenceIndex()
        assert idx.total_entries == 0
        assert idx.verified_count == 0

    def test_as_dict(self):
        e = EvidenceEntry(evidence_id="EV-001", source_runtime="mission")
        idx = EvidenceIndex(entries=(e,), total_entries=1, verified_count=1,
                           traceable_count=1, categories_covered=("inventory",))
        d = idx.as_dict()
        assert d["total_entries"] == 1


# ═══════════════════════════════════════════════════════════
# WP-C1.6: Consumer Integration (endpoint verification)
# ═══════════════════════════════════════════════════════════

class TestObservationWiring:
    """Wiring — singleton, factory, all adapters registered."""

    def test_create_registry(self):
        reg = create_publication_registry()
        assert "mission" in reg.registered_runtimes()
        assert "workflow" in reg.registered_runtimes()
        assert "policy" in reg.registered_runtimes()
        assert "execution" in reg.registered_runtimes()
        assert "approval" in reg.registered_runtimes()
        assert "audit" in reg.registered_runtimes()
        assert "knowledge" in reg.registered_runtimes()
        assert "memory" in reg.registered_runtimes()
        assert "artifact" in reg.registered_runtimes()
        assert "runtime_service" in reg.registered_runtimes()

    def test_singleton_registry(self):
        reg1 = get_publication_registry()
        reg2 = get_publication_registry()
        assert reg1 is reg2

    def test_singleton_gateway(self):
        gw1 = get_observation_gateway()
        gw2 = get_observation_gateway()
        assert gw1 is gw2


class TestObservationResponse:
    """ObservationResponse — DTO."""

    def test_ok_response(self):
        resp = ObservationResponse(status="ok", runtime_count=10,
                                   aggregated_health="healthy")
        d = resp.as_dict()
        assert d["status"] == "ok"
        assert d["runtime_count"] == 10

    def test_not_found_response(self):
        resp = ObservationResponse(status="not_found")
        d = resp.as_dict()
        assert d["status"] == "not_found"
        assert d["runtime_count"] == 0


# ═══════════════════════════════════════════════════════════
# Cross-WP Integration Tests
# ═══════════════════════════════════════════════════════════

class TestCrossWPIntegration:
    """Integration: publication -> timeline -> health -> capability -> evidence."""

    def test_publication_feeds_observation(self):
        """Publication data flows through to ObservationGateway."""
        gw = get_observation_gateway()
        resp = gw.observe_all()
        assert resp.runtime_count == 10
        assert resp.aggregated_health in ("healthy", "degraded", "unhealthy", "unknown")

    def test_health_matrix_matches_publication(self):
        """Health overview must match per-runtime health in publications."""
        gw = get_observation_gateway()
        overview = gw.health_overview()
        resp = gw.observe_all()

        # verify count consistency
        assert overview.healthy_count + overview.degraded_count + \
               overview.unhealthy_count + overview.unknown_count == resp.runtime_count

    def test_capability_matches_publication(self):
        """Capability status must match publication adapters."""
        reader = CapabilityStatusReader()
        matrix = reader.read_all()
        reg = get_publication_registry()

        for cs in matrix.statuses:
            pub = reg.observe(cs.runtime_id)
            assert pub is not None, f"{cs.runtime_id} not in registry"
            assert pub.has_preview == cs.has_preview, \
                f"{cs.runtime_id}: preview mismatch pub={pub.has_preview} cap={cs.has_preview}"
            assert pub.has_metadata == cs.has_metadata, \
                f"{cs.runtime_id}: metadata mismatch"

    def test_timeline_sources_are_in_registry(self):
        """Timeline sources must correspond to registered runtimes."""
        agg = TimelineAggregator()
        agg.collect_all()
        view = agg.view()
        reg = get_publication_registry()

        for src in view.sources_covered:
            if src == "execution":
                assert "execution" in reg.registered_runtimes()
            elif src == "approval":
                assert "approval" in reg.registered_runtimes()
            elif src == "audit":
                assert "audit" in reg.registered_runtimes()
            elif src == "mission":
                assert "mission" in reg.registered_runtimes()

    def test_evidence_sources_are_in_registry(self):
        """Evidence entries must reference registered runtimes."""
        explorer = EvidenceExplorer()
        index = explorer.index_all()
        reg = get_publication_registry()

        for entry in index.entries:
            assert entry.source_runtime in reg.registered_runtimes(), \
                f"Evidence {entry.evidence_id} source '{entry.source_runtime}' not registered"

    def test_read_only_no_mutation(self):
        """Verify all operations are read-only — no runtime state changed."""
        gw = get_observation_gateway()

        # Multiple calls should produce consistent results
        r1 = gw.observe_all()
        r2 = gw.observe_all()
        assert r1.runtime_count == r2.runtime_count
        assert r1.aggregated_health == r2.aggregated_health

    def test_gap_coordinator_wiring(self):
        """C-Phase 2: Gap coordinator accessible via wiring singleton."""
        from sam.runtime_service.api.observation_wiring import (
            get_gap_coordinator, resolve_all_gaps
        )
        coordinator = get_gap_coordinator()
        assert coordinator is not None
        report = coordinator.resolve_all()
        assert report.total_gaps == 6
        assert report.resolved_gaps == 6

    def test_resolve_all_gaps_shortcut(self):
        """C-Phase 2: resolve_all_gaps() shortcut works."""
        from sam.runtime_service.api.observation_wiring import resolve_all_gaps
        report = resolve_all_gaps()
        assert report.unified_health.status == "ok"
        assert report.readiness.status == "ok"
        assert len(report.summary()) > 0
