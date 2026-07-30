import pytest
import os
from dataclasses import FrozenInstanceError

from sam.guardian.live.transition import (
    RuntimeTransition, TransitionType, ImpactLevel,
    TransitionSummary, TransitionStatistics, TransitionHistory,
)
from sam.guardian.live.diff_engine import SnapshotDiffEngine
from sam.guardian.live.change_detector import ChangeDetector
from sam.guardian.live.impact import ImpactAnalyzer
from sam.guardian.live.timeline import TransitionTimeline
from sam.guardian.live.state import (
    RuntimeState, RuntimeStatistics, RuntimeSnapshot,
    RuntimeStatus, RuntimeHealth, RuntimeVersion,
)


# --- DTO immutability ---

def test_transition_frozen():
    t = RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0,
    )
    with pytest.raises(FrozenInstanceError):
        t.transition_id = "changed"


def test_summary_frozen():
    s = TransitionSummary(
        total_transitions=0, transition_counts={}, impact_counts={},
        critical_count=0, high_count=0, medium_count=0, low_count=0,
        period_start=0.0, period_end=0.0, involved_runtimes=[],
    )
    with pytest.raises(FrozenInstanceError):
        s.total_transitions = 10


def test_transition_to_dict():
    t = RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.HEALTH_CHANGED,
        runtime_id="r1", timestamp=100.0, impact=ImpactLevel.HIGH,
    )
    d = t.to_dict()
    assert d["transition_id"] == "t1"
    assert d["transition_type"] == "HEALTH_CHANGED"
    assert d["impact"] == "HIGH"


# --- Diff Engine ---

def test_diff_engine_init():
    de = SnapshotDiffEngine()
    assert de is not None


def test_diff_engine_no_changes():
    de = SnapshotDiffEngine()
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    result = de.diff(snap_a, snap_b)
    assert result["has_changes"] is False


def test_diff_engine_added():
    de = SnapshotDiffEngine()
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    state = RuntimeState(runtime_id="r1")
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={"r1": state}, statistics=RuntimeStatistics.empty(),
    )
    result = de.diff(snap_a, snap_b)
    assert result["has_changes"] is True
    assert "r1" in result["added"]


def test_diff_engine_removed():
    de = SnapshotDiffEngine()
    state = RuntimeState(runtime_id="r1")
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": state}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    result = de.diff(snap_a, snap_b)
    assert result["has_changes"] is True
    assert "r1" in result["removed"]


def test_diff_engine_health_changed():
    de = SnapshotDiffEngine()
    state_a = RuntimeState(runtime_id="r1", health=RuntimeHealth.HEALTHY)
    state_b = RuntimeState(runtime_id="r1", health=RuntimeHealth.CRITICAL)
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": state_a}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={"r1": state_b}, statistics=RuntimeStatistics.empty(),
    )
    result = de.diff(snap_a, snap_b)
    assert result["has_changes"] is True
    assert len(result["changed"]) == 1


def test_diff_engine_multi_snapshots():
    de = SnapshotDiffEngine()
    snaps = []
    for i in range(3):
        snaps.append(RuntimeSnapshot(
            snapshot_id=f"s{i}", timestamp=float(i), total_runtimes=i,
            runtimes={
                f"r{j}": RuntimeState(runtime_id=f"r{j}")
                for j in range(i)
            },
            statistics=RuntimeStatistics.empty(),
        ))
    diffs = de.diff_from_snapshots(snaps)
    assert len(diffs) == 2


# --- Change Detector ---

def test_change_detector_init():
    cd = ChangeDetector()
    assert cd is not None


def test_change_detector_no_changes():
    cd = ChangeDetector()
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    transitions = cd.detect(snap_a, snap_b)
    assert len(transitions) == 0


def test_change_detector_added():
    cd = ChangeDetector()
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    state = RuntimeState(runtime_id="r1")
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={"r1": state}, statistics=RuntimeStatistics.empty(),
    )
    transitions = cd.detect(snap_a, snap_b)
    added = [t for t in transitions if t.transition_type == TransitionType.RUNTIME_ADDED]
    assert len(added) >= 1


def test_change_detector_removed():
    cd = ChangeDetector()
    state = RuntimeState(runtime_id="r1")
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": state}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=0,
        runtimes={}, statistics=RuntimeStatistics.empty(),
    )
    transitions = cd.detect(snap_a, snap_b)
    removed = [t for t in transitions if t.transition_type == TransitionType.RUNTIME_REMOVED]
    assert len(removed) >= 1


def test_change_detector_health_critical():
    cd = ChangeDetector()
    state_a = RuntimeState(runtime_id="r1", health=RuntimeHealth.HEALTHY)
    state_b = RuntimeState(runtime_id="r1", health=RuntimeHealth.CRITICAL)
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": state_a}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={"r1": state_b}, statistics=RuntimeStatistics.empty(),
    )
    transitions = cd.detect(snap_a, snap_b)
    health = [t for t in transitions if t.transition_type == TransitionType.HEALTH_CHANGED]
    assert len(health) >= 1
    if health:
        assert health[0].impact == ImpactLevel.CRITICAL


def test_change_detector_registry():
    cd = ChangeDetector()
    t = cd.detect_registry_change(1, 3)
    assert t is not None
    assert t.transition_type == TransitionType.REGISTRY_CHANGED


def test_change_detector_registry_no_change():
    cd = ChangeDetector()
    t = cd.detect_registry_change(2, 2)
    assert t is None


# --- Impact Analyzer ---

def test_impact_analyzer_init():
    ia = ImpactAnalyzer()
    assert ia is not None


def test_impact_analyzer_critical():
    ia = ImpactAnalyzer()
    t = RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.HEALTH_CHANGED,
        runtime_id="r1", timestamp=0.0, impact=ImpactLevel.LOW,
        details={"field_change": {"field": "health", "to": "CRITICAL"}},
    )
    impact = ia.analyze_transition(t)
    assert impact == ImpactLevel.CRITICAL


def test_impact_analyzer_removed():
    ia = ImpactAnalyzer()
    t = RuntimeTransition(
        transition_id="t2", transition_type=TransitionType.RUNTIME_REMOVED,
        runtime_id="r1", timestamp=0.0,
    )
    assert ia.analyze_transition(t) == ImpactLevel.HIGH


def test_impact_analyzer_batch_empty():
    ia = ImpactAnalyzer()
    result = ia.analyze_batch([])
    assert result["total"] == 0


def test_impact_analyzer_batch():
    ia = ImpactAnalyzer()
    ts = [
        RuntimeTransition(
            transition_id="t1", transition_type=TransitionType.HEALTH_CHANGED,
            runtime_id="r1", timestamp=0.0,
            details={"field_change": {"field": "health", "to": "CRITICAL"}},
        ),
        RuntimeTransition(
            transition_id="t2", transition_type=TransitionType.RUNTIME_ADDED,
            runtime_id="r2", timestamp=1.0,
        ),
    ]
    result = ia.analyze_batch(ts)
    assert result["total"] == 2
    assert result["has_critical"] is True


# --- Timeline ---

def test_timeline_init():
    tl = TransitionTimeline()
    assert tl.count == 0
    assert tl.latest is None


def test_timeline_record():
    tl = TransitionTimeline()
    t = RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0,
    )
    tl.record(t)
    assert tl.count == 1
    assert tl.latest is not None


def test_timeline_record_batch():
    tl = TransitionTimeline()
    ts = [
        RuntimeTransition(transition_id=f"t{i}", transition_type=TransitionType.RUNTIME_ADDED,
                          runtime_id="r1", timestamp=float(i))
        for i in range(5)
    ]
    tl.record_batch(ts)
    assert tl.count == 5


def test_timeline_lookup():
    tl = TransitionTimeline()
    t = RuntimeTransition(
        transition_id="find-me", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0,
    )
    tl.record(t)
    found = tl.lookup("find-me")
    assert found is not None
    assert found.transition_id == "find-me"


def test_timeline_filter_by_type():
    tl = TransitionTimeline()
    tl.record(RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0,
    ))
    tl.record(RuntimeTransition(
        transition_id="t2", transition_type=TransitionType.HEALTH_CHANGED,
        runtime_id="r1", timestamp=1.0,
    ))
    filtered = tl.filter(transition_type=TransitionType.HEALTH_CHANGED)
    assert len(filtered) == 1


def test_timeline_filter_by_impact():
    tl = TransitionTimeline()
    tl.record(RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.HEALTH_CHANGED,
        runtime_id="r1", timestamp=0.0, impact=ImpactLevel.CRITICAL,
    ))
    tl.record(RuntimeTransition(
        transition_id="t2", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r2", timestamp=1.0, impact=ImpactLevel.LOW,
    ))
    critical = tl.filter(min_impact=ImpactLevel.HIGH)
    assert len(critical) == 1


def test_timeline_get_summary():
    tl = TransitionTimeline()
    tl.record(RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0, impact=ImpactLevel.LOW,
    ))
    summary = tl.get_summary()
    assert summary.total_transitions == 1


def test_timeline_get_statistics():
    tl = TransitionTimeline()
    tl.record(RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0, impact=ImpactLevel.LOW,
    ))
    stats = tl.get_statistics()
    assert stats.total_transitions == 1


def test_timeline_clear():
    tl = TransitionTimeline()
    tl.record(RuntimeTransition(
        transition_id="t1", transition_type=TransitionType.RUNTIME_ADDED,
        runtime_id="r1", timestamp=0.0,
    ))
    tl.clear()
    assert tl.count == 0


def test_timeline_max_size():
    tl = TransitionTimeline(max_size=3)
    for i in range(10):
        tl.record(RuntimeTransition(
            transition_id=f"t{i}", transition_type=TransitionType.RUNTIME_ADDED,
            runtime_id="r1", timestamp=float(i),
        ))
    assert tl.count <= 3


# --- Conversation Transition ---

def test_conversation_transition_query_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-query")
    assert runtime.conversation_transition.query_count == 10


def test_conversation_transition_latest():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-latest")
    result = runtime.conversation_transition.latest_transition()
    assert result["has_transition"] is False


def test_conversation_transition_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-hist")
    result = runtime.conversation_transition.transition_history()
    assert result["total"] == 0


def test_conversation_transition_critical():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-crit")
    result = runtime.conversation_transition.critical_changes()
    assert result["count"] == 0


def test_conversation_transition_runtime():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-rt")
    result = runtime.conversation_transition.runtime_changes("r1")
    assert result["runtime_id"] == "r1"


def test_conversation_transition_health():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-health")
    result = runtime.conversation_transition.health_changes()
    assert result["count"] == 0


def test_conversation_transition_version():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-ver")
    result = runtime.conversation_transition.version_changes()
    assert result["count"] == 0


def test_conversation_transition_timeline():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-tl")
    result = runtime.conversation_transition.timeline()
    assert "summary" in result


def test_conversation_transition_impact():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-im")
    result = runtime.conversation_transition.impact()
    assert "analysis" in result


def test_conversation_transition_summary():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="ct-sum")
    result = runtime.conversation_transition.summary()
    assert "summary" in result
    assert "impact" in result


# --- Dashboard Transition ---

def test_dashboard_transition_card_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-count")
    assert runtime.dashboard_transition.card_count == 6


def test_dashboard_transition_recent_changes():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-rc")
    card = runtime.dashboard_transition.get_recent_changes_card()
    assert card.total_transitions == 0


def test_dashboard_transition_impact():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-im")
    card = runtime.dashboard_transition.get_impact_card()
    assert isinstance(card.has_critical, bool)


def test_dashboard_transition_timeline():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-tl")
    card = runtime.dashboard_transition.get_timeline_card()
    assert card.total_events == 0


def test_dashboard_transition_critical_events():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-ce")
    card = runtime.dashboard_transition.get_critical_events_card()
    assert card.critical_count == 0


def test_dashboard_transition_statistics():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-st")
    card = runtime.dashboard_transition.get_transition_statistics_card()
    assert card.total_transitions == 0


def test_dashboard_transition_evolution():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-ev")
    card = runtime.dashboard_transition.get_runtime_evolution_card()
    assert card.runtimes_count == 0


def test_dashboard_transition_all_cards():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    runtime = GuardianLiveRuntime(runtime_id="dt-all")
    cards = runtime.dashboard_transition.get_all_cards()
    assert len(cards) == 6


# --- Pipeline integration ---

def test_full_pipeline_with_transition():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class TSub(GuardianEventSubscriber):
        def supports(self, e):
            return True
        def handle(self, e):
            return {"handled": True}

    runtime = GuardianLiveRuntime(runtime_id="pipeline-trans")
    runtime.start()
    runtime.register_subscriber(TSub())

    # First run: no transitions yet (need 2+ snapshots)
    r1 = runtime.execute_pipeline({"test": 1})
    assert r1["is_running"]
    assert r1["transition_count"] == 0

    # Second run: should detect transitions now
    r2 = runtime.execute_pipeline({"test": 2})
    assert r2["is_running"]

    runtime.stop()


def test_pipeline_transition_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class TSub(GuardianEventSubscriber):
        def supports(self, e):
            return True
        def handle(self, e):
            return {"handled": True}

    runtime = GuardianLiveRuntime(runtime_id="pipeline-count")
    runtime.start()
    runtime.register_subscriber(TSub())
    for i in range(3):
        runtime.execute_pipeline({"i": i})
    status = runtime.get_status()
    assert "transition_count" in status
    assert "critical_transitions" in status
    runtime.stop()


def test_change_detector_health_degraded():
    cd = ChangeDetector()
    state_a = RuntimeState(runtime_id="r1", health=RuntimeHealth.HEALTHY)
    state_b = RuntimeState(runtime_id="r1", health=RuntimeHealth.DEGRADED)
    snap_a = RuntimeSnapshot(
        snapshot_id="s1", timestamp=0.0, total_runtimes=1,
        runtimes={"r1": state_a}, statistics=RuntimeStatistics.empty(),
    )
    snap_b = RuntimeSnapshot(
        snapshot_id="s2", timestamp=1.0, total_runtimes=1,
        runtimes={"r1": state_b}, statistics=RuntimeStatistics.empty(),
    )
    transitions = cd.detect(snap_a, snap_b)
    health = [t for t in transitions if t.transition_type == TransitionType.HEALTH_CHANGED]
    if health:
        assert health[0].impact == ImpactLevel.HIGH


# --- Forbidden import scanning ---

FORBIDDEN_PATTERNS = [
    "from sam.domain", "from sam.repository", "from sam.storage",
    "from sam.operations", "import threading", "import asyncio",
    "async def", "await ", "import socket", "import websockets",
    "from websocket", "import multiprocessing",
]


def test_forbidden_imports():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    sprint45_files = [
        "transition.py", "diff_engine.py", "change_detector.py",
        "impact.py", "timeline.py",
        "conversation_transition.py", "dashboard_transition.py",
    ]
    for fname in sprint45_files:
        path = os.path.join(live_path, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            for pattern in FORBIDDEN_PATTERNS:
                assert pattern not in text, f"Forbidden '{pattern}' in {fname}"


def test_no_async():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    sprint45_files = [
        "transition.py", "diff_engine.py", "change_detector.py",
        "impact.py", "timeline.py",
        "conversation_transition.py", "dashboard_transition.py",
    ]
    for fname in sprint45_files:
        path = os.path.join(live_path, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            assert "async def" not in text, f"async in {fname}"
            assert "await " not in text, f"await in {fname}"


@pytest.mark.parametrize("i", list(range(80)))
def test_deterministic_transition(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber

    class DSub(GuardianEventSubscriber):
        def supports(self, e):
            return True
        def handle(self, e):
            return {"handled": i}

    runtime = GuardianLiveRuntime(runtime_id=f"det-trans-{i:03d}")
    runtime.start()
    runtime.register_subscriber(DSub())
    for _ in range(2):
        runtime.execute_pipeline({"idx": i})
    assert runtime.timeline is not None
    runtime.stop()
