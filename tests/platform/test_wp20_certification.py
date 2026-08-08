# -*- coding: utf-8 -*-
"""IP-3.5-002 Mission Experience - Certification (WP-09..16).

Menguji: Mission Workspace (WP-09), Mission Timeline (WP-10), Mission
Journey (WP-11), Mission Progress (WP-12), Mission Context (WP-13),
Mission Insight (WP-14), Mission API (WP-15), Mission Compliance (WP-16).

Guardrail yang diverifikasi (MEX-01..10): Mission Experience PRESENTS
mission, TIDAK mengeksekusi/memodifikasi mission runtime. Seluruh input
mission DIBERIKAN dari luar (governed runtime service), bukan ditarik.
"""

import pytest

from sam.platform import (
    MissionAPI,
    MissionContext,
    MissionHealthInput,
    MissionInput,
    MissionInsight,
    MissionJourney,
    MissionJourneyStep,
    MissionProgress,
    MissionSnapshot,
    MissionTimelineInput,
    MissionTimelineView,
    MissionWorkspaceView,
    build_insight,
    build_journey,
    compute_progress,
    mission_compliance_check,
    timeline_from_checkpoints,
)


# --- WP-09 Mission Workspace ------------------------------------------------

def test_mission_input_requires_id():
    with pytest.raises(ValueError):
        MissionInput(mission_id="")


def test_mission_input_clamps_progress():
    assert MissionInput("m", progress=-1.0).progress == 0.0
    assert MissionInput("m", progress=2.5).progress == 1.0


def test_mission_workspace_view_lookup():
    view = MissionWorkspaceView(
        missions=(MissionInput("m1", "A"), MissionInput("m2", "B")),
    )
    assert view.mission("m2").title == "B"
    assert view.mission("nope") is None
    assert view.journey("m1") is None  # tidak ada journey -> None


# --- WP-10 Mission Timeline -------------------------------------------------

def test_timeline_view_current_index_clamped():
    tv = MissionTimelineView("m", ("a", "b", "c"), current_index=99)
    assert tv.current_index == 2  # clamp ke len-1
    tv2 = MissionTimelineView("m", ("a", "b"), current_index=-5)
    assert tv2.current_index == -1


def test_timeline_is_complete():
    assert MissionTimelineView("m", ("a", "b"), current_index=1).is_complete()
    assert not MissionTimelineView("m", ("a", "b"), current_index=0).is_complete()


def test_timeline_from_checkpoints():
    tv = timeline_from_checkpoints("m", ["x", "y"], current_index=1)
    assert tv.checkpoints == ("x", "y")
    assert tv.current_index == 1


# --- WP-11 Mission Journey --------------------------------------------------

def test_journey_from_checkpoints():
    j = build_journey("m", ("plan", "build", "verify"))
    assert j.total_count() == 3
    assert j.completed_count() == 0
    assert j.steps[1].order == 1
    assert j.steps[1].label == "build"


def test_journey_completion_ratio():
    j = MissionJourney("m", (MissionJourneyStep("a", 0, True),
                             MissionJourneyStep("b", 1, False)))
    assert j.completion_ratio() == 0.5
    assert MissionJourney("m").completion_ratio() == 0.0  # kosong -> 0


# --- WP-12 Mission Progress -------------------------------------------------

def test_compute_progress():
    assert compute_progress("m", 3, 4).progress == 0.75
    assert compute_progress("m", 0, 0).progress == 0.0  # total 0 -> 0
    assert compute_progress("m", 10, 5).progress == 1.0  # clamp


def test_progress_percent():
    assert MissionProgress("m", 0.5).percent == 50.0


# --- WP-13 Mission Context --------------------------------------------------

def test_context_with_active_and_focus():
    ctx = MissionContext(active_mission_id="m1", focus_mission_id="m2")
    assert ctx.with_active("m3").active_mission_id == "m3"
    assert ctx.with_focus("m4").focus_mission_id == "m4"
    # empty tidak mengubah
    assert ctx.with_active("").active_mission_id == "m1"


# --- WP-14 Mission Insight --------------------------------------------------

def test_build_insight():
    ms = (MissionInput("m1", state="active", progress=0.5),
          MissionInput("m2", state="complete", progress=1.0))
    ins = build_insight(ms)
    assert ins.total_missions == 2
    assert ins.active_count == 1
    assert ins.complete_count == 1
    assert ins.average_progress == 0.75
    assert ins.has_data


def test_build_insight_empty():
    ins = build_insight([])
    assert ins.total_missions == 0
    assert ins.average_progress == 0.0
    assert not ins.has_data


# --- WP-15 Mission API ------------------------------------------------------

def _setup_api():
    api = MissionAPI()
    api.register_mission(MissionInput("m1", "Alpha", state="active",
                                      stage="execution", progress=0.6))
    api.register_mission(MissionInput("m2", "Beta", state="complete",
                                      progress=1.0))
    api.register_timeline(MissionTimelineInput("m1", ("plan", "build", "verify")))
    api.register_health(MissionHealthInput("m1", state="healthy", checks=("cpu",)))
    j = build_journey("m2", ("init", "done"))
    api.register_journey(j)
    return api


def test_api_snapshot_mission():
    api = _setup_api()
    snap = api.snapshot("m1")
    assert isinstance(snap, MissionSnapshot)
    assert snap.title == "Alpha"
    assert snap.state == "active"
    assert snap.progress == 0.6
    assert snap.journey.total_count() == 3
    assert snap.health_state == "healthy"
    assert snap.health_checks == ("cpu",)


def test_api_snapshot_missing():
    api = _setup_api()
    assert api.snapshot("ghost") is None


def test_api_insights_and_ids():
    api = _setup_api()
    ins = api.insights()
    assert ins.total_missions == 2
    assert api.mission_ids() == ("m1", "m2")
    assert api.view().mission("m1").title == "Alpha"


def test_api_snapshot_builds_journey_from_timeline():
    # mission tanpa journey explisit -> journey dibangun dari timeline
    api = _setup_api()
    snap = api.snapshot("m1")
    assert snap.journey.steps[0].label == "plan"


# --- WP-16 Mission Compliance ----------------------------------------------

def test_mission_compliance_passes():
    res = mission_compliance_check()
    assert res.ok, res.messages
    assert res.group == "MEX"
    assert res.forbidden_found == ()


# --- Exit criteria: presentation-passive mission ----------------------------

def test_mission_api_has_no_execution_verbs():
    names = [n for n in dir(MissionAPI) if not n.startswith("_")]
    forbidden = {"run_mission", "execute_mission", "start_mission",
                 "advance_mission", "coordinate_mission", "allocate_resource"}
    assert not (forbidden & set(names))
