"""Sprint 107 — Runtime Scheduler Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_scheduler import (
    ScheduleSlot, SchedulePlan, ScheduleWindow, TaskSlot, ScheduleResult,
)
from sam.runtime_kernel.scheduler_engine import SchedulerEngine
from sam.runtime_kernel.task_scheduler import TaskScheduler
from sam.runtime_kernel.window_scheduler import WindowScheduler
from sam.runtime_kernel.priority_allocator import PriorityAllocator
from sam.runtime_kernel.conversation_scheduler import ConversationScheduler, DashboardScheduler
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestScheduleSlot:
    def test_create(self):
        s = ScheduleSlot("s1", "guardian", 5, False)
        assert not s.allocated

    def test_immutable(self):
        s = ScheduleSlot("s")
        with pytest.raises(FrozenInstanceError):
            s.allocated = True


class TestSchedulePlan:
    def test_create(self):
        p = SchedulePlan("p1", total_slots=5, allocated_slots=2)
        assert not p.is_full

    def test_full(self):
        p = SchedulePlan("p1", total_slots=2, allocated_slots=2, is_full=True)
        assert p.is_full

    def test_immutable(self):
        p = SchedulePlan("p")
        with pytest.raises(FrozenInstanceError):
            p.is_full = True


class TestScheduleWindow:
    def test_create(self):
        w = ScheduleWindow("w1", 0.0, 100.0, "guardian")
        assert w.subsystem == "guardian"

    def test_immutable(self):
        w = ScheduleWindow("w")
        with pytest.raises(FrozenInstanceError):
            w.subsystem = "new"


class TestTaskSlot:
    def test_create(self):
        t = TaskSlot("t1", "boot", 1, "pending")
        assert t.status == "pending"

    def test_immutable(self):
        t = TaskSlot("t")
        with pytest.raises(FrozenInstanceError):
            t.status = "running"


class TestScheduleResult:
    def test_created(self):
        r = ScheduleResult("r1", True, "s1")
        assert r.scheduled

    def test_immutable(self):
        r = ScheduleResult("r")
        with pytest.raises(FrozenInstanceError):
            r.scheduled = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestSchedulerEngine:
    def test_create_plan(self):
        e = SchedulerEngine()
        p = e.create_plan("p1")
        assert e.count() == 1

    def test_create_with_slots(self):
        e = SchedulerEngine()
        slots = [ScheduleSlot("s1", "g", 1), ScheduleSlot("s2", "d", 2)]
        p = e.create_plan("p1", slots)
        assert p.total_slots == 2

    def test_allocate(self):
        e = SchedulerEngine()
        slots = [ScheduleSlot("s1", "g", 1)]
        e.create_plan("p1", slots)
        r = e.allocate("p1", "s1")
        assert r.scheduled
        p = e.get_plan("p1")
        assert p is not None
        assert p.allocated_slots == 1
        assert p.is_full

    def test_allocate_not_found(self):
        e = SchedulerEngine()
        e.create_plan("p1")
        r = e.allocate("p1", "bogus")
        assert not r.scheduled

    def test_allocate_missing_plan(self):
        e = SchedulerEngine()
        r = e.allocate("bogus", "s1")
        assert not r.scheduled

    def test_get_plan(self):
        e = SchedulerEngine()
        e.create_plan("p1")
        assert e.get_plan("p1") is not None
        assert e.get_plan("bogus") is None

    def test_create_full_plan(self):
        e = SchedulerEngine()
        slots = [ScheduleSlot("s1", "g", 1, True)]
        p = e.create_plan("p1", slots)
        assert p.is_full


class TestTaskScheduler:
    def test_add(self):
        s = TaskScheduler()
        s.add(TaskSlot("t1", "boot", 1))
        assert s.count() == 1

    def test_get(self):
        s = TaskScheduler()
        s.add(TaskSlot("t1", "boot", 1))
        assert s.get("t1") is not None
        assert s.get("bogus") is None

    def test_mark_running(self):
        s = TaskScheduler()
        s.add(TaskSlot("t1", "boot", 1))
        t = s.mark_running("t1")
        assert t is not None
        assert t.status == "running"

    def test_mark_complete(self):
        s = TaskScheduler()
        s.add(TaskSlot("t1", "boot", 1))
        t = s.mark_complete("t1")
        assert t is not None
        assert t.status == "completed"

    def test_mark_missing(self):
        s = TaskScheduler()
        assert s.mark_running("bogus") is None
        assert s.mark_complete("bogus") is None

    def test_list_pending(self):
        s = TaskScheduler()
        s.add(TaskSlot("t1", "a", 1))
        s.add(TaskSlot("t2", "b", 2))
        s.mark_running("t1")
        assert len(s.list_pending()) == 1


class TestWindowScheduler:
    def test_add(self):
        w = WindowScheduler()
        w.add(ScheduleWindow("w1", 0.0, 100.0, "guardian"))
        assert w.count() == 1

    def test_get(self):
        w = WindowScheduler()
        w.add(ScheduleWindow("w1", 0.0, 100.0, "guardian"))
        assert w.get("w1") is not None
        assert w.get("bogus") is None

    def test_find_by_subsystem(self):
        w = WindowScheduler()
        w.add(ScheduleWindow("w1", 0.0, 100.0, "guardian"))
        w.add(ScheduleWindow("w2", 0.0, 200.0, "decision"))
        assert len(w.find_by_subsystem("guardian")) == 1


class TestPriorityAllocator:
    def test_allocate_slots(self):
        a = PriorityAllocator()
        slots = [ScheduleSlot("s1", "g", 0, False), ScheduleSlot("s2", "d", 0, False)]
        tasks = [TaskSlot("t1", "boot", 5), TaskSlot("t2", "config", 3)]
        result = a.allocate_slots(slots, tasks)
        assert result[0].allocated
        assert result[0].priority == 5

    def test_get_highest_priority(self):
        a = PriorityAllocator()
        slots = [ScheduleSlot("s1", "g", 1), ScheduleSlot("s2", "d", 5)]
        assert a.get_highest_priority(slots) == 5

    def test_get_highest_empty(self):
        a = PriorityAllocator()
        assert a.get_highest_priority([]) == 0


# ============================================================
# 3. Conversation Scheduler
# ============================================================

class TestConversationScheduler:
    def test_queries(self):
        cs = ConversationScheduler(SchedulerEngine(), TaskScheduler(),
                                   WindowScheduler(), PriorityAllocator())
        assert cs.get_engine() is not None
        assert cs.get_task_scheduler() is not None
        assert cs.get_window_scheduler() is not None
        assert cs.get_priority_allocator() is not None
        layers = cs.describe_layers()
        assert len(layers) == 4
        assert cs.count_layers() == 4
        assert cs.get_plan_count() == 0
        assert cs.get_task_count() == 0


# ============================================================
# 4. Dashboard Scheduler
# ============================================================

class TestDashboardScheduler:
    def test_cards(self):
        ds = DashboardScheduler(SchedulerEngine(), TaskScheduler())
        for card in [ds.engine_card(), ds.plan_card(), ds.task_card(),
                     ds.window_card(), ds.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        ds = DashboardScheduler(SchedulerEngine(), TaskScheduler())
        for card in [ds.engine_card(), ds.plan_card(), ds.task_card(),
                     ds.window_card(), ds.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        ScheduleSlot("s"),
        SchedulePlan("p"),
        ScheduleWindow("w"),
        TaskSlot("t"),
        ScheduleResult("r"),
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
        src_dir = pathlib.Path("src/sam/runtime_kernel")
        if not src_dir.exists():
            pytest.skip("runtime_kernel dir not found")
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
# 7. Parametrized
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_plan_parametrized(i):
    e = SchedulerEngine()
    slots = [ScheduleSlot(f"s{j}", f"sub{j}", j) for j in range(i % 6 + 1)]
    p = e.create_plan(f"p{i}", slots)
    assert p.total_slots == i % 6 + 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_task_parametrized(i):
    s = TaskScheduler()
    s.add(TaskSlot(f"t{i}", f"Task {i}", i % 5, "pending"))
    assert s.count() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_window_parametrized(i):
    w = WindowScheduler()
    w.add(ScheduleWindow(f"w{i}", float(i * 10), float(i * 10 + 50), f"sub{i % 4}"))
    assert w.count() == 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_allocate_parametrized(i):
    e = SchedulerEngine()
    slots = [ScheduleSlot(f"s{j}", f"sub{j}", j, False) for j in range(i % 4 + 1)]
    e.create_plan("p1", slots)
    for j in range(i % 4 + 1):
        r = e.allocate("p1", f"s{j}")
        assert r.scheduled
    p = e.get_plan("p1")
    assert p is not None
    assert p.is_full == (i % 4 + 1 > 0)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_allocator_parametrized(i):
    a = PriorityAllocator()
    slots = [ScheduleSlot(f"s{j}", f"sub{j}", 0, False) for j in range(3)]
    tasks = [TaskSlot(f"t{j}", f"Task{j}", i * j) for j in range(3)]
    result = a.allocate_slots(slots, tasks)
    assert sum(1 for s in result if s.allocated) == min(3, 3)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cs = ConversationScheduler(SchedulerEngine(), TaskScheduler(),
                               WindowScheduler(), PriorityAllocator())
    assert cs.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_dashboard_parametrized(i):
    ds = DashboardScheduler(SchedulerEngine(), TaskScheduler())
    c = ds.engine_card()
    assert c.status == "ready"
