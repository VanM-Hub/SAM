"""Tests for C-Phase 3 (Workstream C1): Mission Operational Intelligence.

Memverifikasi observer Mission menghasilkan observasi operasional Mission
(Timeline/Status/Progress/Health) secara read-only murni, tanpa mutasi
registry maupun governance.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.mission_intelligence import (
    MissionCheckpointView,
    MissionHealthView,
    MissionIntelligenceObserver,
    MissionIntelligenceReport,
    MissionProgressView,
    MissionStatusView,
    MissionTimelineView,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _registry_with_mission() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="mission",
        health_state="healthy",
        readiness_level="operational",
        operational_state="ready",
        metric_count=5,
        dashboard_count=10,
        health_check_count=1,
        snapshot_count=2,
        timeline_events=8,
        has_preview=True,
        has_metadata=True,
        has_lifecycle=False,
    )))
    return reg


class TestMissionTimeline:
    def test_builds_five_checkpoints(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        tl = ob.timeline()
        assert tl.checkpoint_count == 5
        assert tl.checkpoints[0].label == "plan"
        assert tl.checkpoints[-1].label == "close"

    def test_checkpoint_is_immutable_dto(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        cp = ob.timeline().checkpoints[0]
        assert isinstance(cp, MissionCheckpointView)
        assert cp.order == 0
        assert "checkpoint_id" in cp.as_dict()


class TestMissionStatus:
    def test_status_ready(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        st = ob.status()
        assert isinstance(st, MissionStatusView)
        assert st.state == "ready"
        assert st.ready is True


class TestMissionProgress:
    def test_progress_ratio(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        pr = ob.progress()
        assert isinstance(pr, MissionProgressView)
        assert pr.total_checkpoints == 5
        assert 0.0 <= pr.progress_ratio <= 1.0
        assert pr.completed_checkpoints == 1  # label close


class TestMissionHealth:
    def test_health_healthy(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        h = ob.health()
        assert isinstance(h, MissionHealthView)
        assert h.healthy is True


class TestMissionDashboard:
    def test_dashboard_aggregates_all(self):
        ob = MissionIntelligenceObserver(_registry_with_mission())
        rep = ob.dashboard()
        assert isinstance(rep, MissionIntelligenceReport)
        assert rep.timeline is not None
        assert rep.status is not None
        assert rep.progress is not None
        assert rep.health is not None
        d = rep.as_dict()
        assert d["mission_id"] == "mission"
        assert d["timeline"]["checkpoint_count"] == 5


class TestMissionReadOnly:
    def test_registry_unchanged_after_observe(self):
        reg = _registry_with_mission()
        before = reg.observe_all().runtime_count
        ob = MissionIntelligenceObserver(reg)
        ob.dashboard(); ob.timeline(); ob.status(); ob.progress(); ob.health()
        after = reg.observe_all().runtime_count
        assert before == after == 1
