"""Sprint 93 — Execution Timeline Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.timeline import (
    Timeline, TimelineEvent, ExecutionWindow, Milestone, TimelineSnapshot,
)
from sam.execution.runtime.timeline_builder import TimelineBuilder
from sam.execution.runtime.conversation_timeline import ConversationTimeline, DashboardTimeline
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Timeline DTO Tests
# ============================================================

class TestTimelineEvent:
    def test_create(self):
        e = TimelineEvent("ev1", 100.0, "execute", candidate_ids=("c1",))
        assert e.event_id == "ev1"
        assert e.timestamp == 100.0
        assert e.event_type == "execute"
        assert e.candidate_ids == ("c1",)

    def test_immutable(self):
        e = TimelineEvent("e", 0.0, "t")
        with pytest.raises(FrozenInstanceError):
            e.event_id = "changed"


class TestTimeline:
    def test_empty(self):
        t = Timeline("tl1", "eo1")
        assert t.total_events == 0
        assert t.estimated_duration == 0.0

    def test_with_events(self):
        e1 = TimelineEvent("ev1", 0.0, "start")
        e2 = TimelineEvent("ev2", 10.0, "end")
        t = Timeline("tl1", "eo1", events=(e1, e2), total_events=2,
                    start_time=0.0, end_time=10.0, estimated_duration=10.0)
        assert t.total_events == 2
        assert t.estimated_duration == 10.0

    def test_immutable(self):
        t = Timeline("t", "e")
        with pytest.raises(FrozenInstanceError):
            t.total_events = 5


class TestExecutionWindow:
    def test_create(self):
        w = ExecutionWindow("w1", "tl1", 0.0, 100.0, candidate_ids=("c1", "c2"))
        assert w.window_id == "w1"
        assert w.start_time == 0.0
        assert w.end_time == 100.0
        assert len(w.candidate_ids) == 2

    def test_immutable(self):
        w = ExecutionWindow("w", "t", 0.0, 1.0)
        with pytest.raises(FrozenInstanceError):
            w.window_id = "changed"


class TestMilestone:
    def test_create(self):
        m = Milestone("m1", 50.0, "Phase 1 Complete", milestone_type="checkpoint")
        assert m.milestone_id == "m1"
        assert m.timestamp == 50.0
        assert m.name == "Phase 1 Complete"

    def test_immutable(self):
        m = Milestone("m", 0.0, "test")
        with pytest.raises(FrozenInstanceError):
            m.milestone_id = "changed"


class TestTimelineSnapshot:
    def test_create(self):
        s = TimelineSnapshot("tl1", total_events=10, total_windows=3, status="ready")
        assert s.total_events == 10
        assert s.status == "ready"

    def test_defaults(self):
        s = TimelineSnapshot("tl1")
        assert s.status == "pending"

    def test_immutable(self):
        s = TimelineSnapshot("t")
        with pytest.raises(FrozenInstanceError):
            s.status = "ready"


# ============================================================
# 2. TimelineBuilder Tests
# ============================================================

class TestTimelineBuilder:
    def test_build_empty(self):
        b = TimelineBuilder()
        t = b.build("tl1", "eo1", [])
        assert t.total_events == 0
        assert t.estimated_duration == 0.0

    def test_build_with_candidates(self):
        b = TimelineBuilder()
        c = [
            ExecutionCandidate("c1", "e1", "r1", 1.0, name="Task 1",
                              estimated_effort=5.0),
            ExecutionCandidate("c2", "e1", "r1", 2.0, name="Task 2",
                              estimated_effort=10.0),
        ]
        t = b.build("tl1", "eo1", c, start_time=100.0)
        assert t.total_events == 2
        assert t.start_time == 100.0
        assert t.estimated_duration == 15.0
        assert t.end_time == 115.0

    def test_build_events(self):
        b = TimelineBuilder()
        c = [
            ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0,
                              candidate_type="batch"),
        ]
        t = b.build("tl1", "eo1", c)
        assert t.events[0].event_type == "batch"
        assert "c1" in t.events[0].candidate_ids

    def test_create_window(self):
        b = TimelineBuilder()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0)]
        w = b.create_window("w1", "tl1", 0.0, 100.0, c, window_type="validation")
        assert w.window_type == "validation"
        assert len(w.candidate_ids) == 1

    def test_create_milestone(self):
        b = TimelineBuilder()
        m = b.create_milestone("m1", 50.0, "Halfway", "50% complete", "checkpoint")
        assert m.name == "Halfway"
        assert m.milestone_type == "checkpoint"

    def test_snapshot(self):
        b = TimelineBuilder()
        t = b.build("tl1", "eo1", [ExecutionCandidate("c1", "e1", "r1", 1.0)])
        w = b.create_window("w1", "tl1", 0.0, 10.0, [])
        m = b.create_milestone("m1", 5.0, "Mid")
        s = b.snapshot(t, [w], [m])
        assert s.total_events == 1
        assert s.total_windows == 1
        assert s.total_milestones == 1
        assert s.status == "ready"


# ============================================================
# 3. ConversationTimeline Tests
# ============================================================

class TestConversationTimeline:
    def test_queries(self):
        ct = ConversationTimeline(TimelineBuilder())
        assert ct.get_builder() is not None
        types = ct.describe_types()
        assert len(types) == 4
        assert ct.count_components() == 4
        events = ct.get_supported_event_types()
        assert len(events) == 5
        windows = ct.get_supported_window_types()
        assert len(windows) == 4
        milestones = ct.get_milestone_types()
        assert len(milestones) == 4


# ============================================================
# 4. DashboardTimeline Tests
# ============================================================

class TestDashboardTimeline:
    def test_cards(self):
        dt = DashboardTimeline(TimelineBuilder())
        tc = dt.timeline_card()
        assert tc.status == "ready"
        wc = dt.windows_card()
        assert wc.metrics["window_types"] == 4
        mc = dt.milestones_card()
        assert mc.metrics["milestone_types"] == 4
        sc = dt.snapshot_card()
        assert sc.status == "pending"
        sumc = dt.summary_card()
        assert sc.status == "pending"

    def test_all_frozen(self):
        dt = DashboardTimeline(TimelineBuilder())
        for card in [dt.timeline_card(), dt.windows_card(), dt.milestones_card(),
                     dt.snapshot_card(), dt.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        TimelineEvent("e", 0.0, "t"),
        Timeline("t", "e"),
        ExecutionWindow("w", "t", 0.0, 1.0),
        Milestone("m", 0.0, "n"),
        TimelineSnapshot("t"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 6. Forbidden Imports
# ============================================================

class TestForbiddenImports:
    def test_0_forbidden_imports(self):
        import ast, pathlib
        forbidden = [
            "asyncio", "threading", "multiprocessing", "socket",
            "http", "urllib", "requests", "aiohttp",
            "subprocess", "os.system", "shutil",
            "sqlite3", "mysql", "postgresql",
            "redis", "celery", "rabbitmq", "kafka",
        ]
        src_dir = pathlib.Path("src/sam/execution/runtime")
        errors = []
        for f in sorted(src_dir.glob("*.py")):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: from {node.module}")
        assert not errors, f"Forbidden imports found: {errors}"


# ============================================================
# 7. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 26)))
def test_timeline_build_parametrized(i):
    b = TimelineBuilder()
    c = [
        ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j * 2))
        for j in range(i % 8 + 1)
    ]
    t = b.build(f"tl{i}", "eo1", c, start_time=float(i * 10))
    assert t.total_events == len(c)
    assert t.start_time == float(i * 10)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_window_parametrized(i):
    b = TimelineBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j)) for j in range(i % 3 + 1)]
    w = b.create_window(f"w{i}", "tl1", float(i), float(i * 10), c)
    assert w.start_time == float(i)
    assert w.end_time == float(i * 10)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_milestone_parametrized(i):
    b = TimelineBuilder()
    types = ["checkpoint", "approval", "review", "handoff"]
    m = b.create_milestone(f"m{i}", float(i * 10), f"Milestone {i}",
                          milestone_type=types[i % len(types)])
    assert m.milestone_type == types[i % len(types)]


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_snapshot_parametrized(i):
    b = TimelineBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j)) for j in range(i % 5 + 1)]
    t = b.build(f"tl{i}", "eo1", c)
    w = b.create_window(f"w{i}", f"tl{i}", 0.0, float(i), c)
    m = b.create_milestone(f"m{i}", float(i), "M")
    s = b.snapshot(t, [w], [m])
    assert s.total_events == len(c)
    assert s.total_windows == 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_timeline_parametrized(i):
    ct = ConversationTimeline(TimelineBuilder())
    assert ct.count_components() == 4
    assert len(ct.get_supported_event_types()) == 5


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_dashboard_timeline_parametrized(i):
    dt = DashboardTimeline(TimelineBuilder())
    c = dt.timeline_card()
    assert c.status == "ready"
