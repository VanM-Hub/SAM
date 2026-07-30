"""Sprint 109 — Runtime Coordinator Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_coordinator import (
    CoordinationTask, CoordinationPlan, SyncPoint,
    OrchestrationOrder, CoordinationResult,
)
from sam.runtime_kernel.coordination_engine import CoordinationEngine
from sam.runtime_kernel.sync_coordinator import SyncCoordinator
from sam.runtime_kernel.orchestrator import Orchestrator
from sam.runtime_kernel.conversation_coordinator import ConversationCoordinator, DashboardCoordinator
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestCoordinationTask:
    def test_create(self):
        t = CoordinationTask("t1", "guardian", "boot", "pending", 1)
        assert t.action == "boot"

    def test_immutable(self):
        t = CoordinationTask("t", "g")
        with pytest.raises(FrozenInstanceError):
            t.status = "completed"


class TestCoordinationPlan:
    def test_create(self):
        p = CoordinationPlan("p1", total=3, completed=1)
        assert not p.is_ready

    def test_immutable(self):
        p = CoordinationPlan("p")
        with pytest.raises(FrozenInstanceError):
            p.is_ready = True


class TestSyncPoint:
    def test_create(self):
        s = SyncPoint("s1", "guardian", False, "data")
        assert not s.synced

    def test_immutable(self):
        s = SyncPoint("s", "g")
        with pytest.raises(FrozenInstanceError):
            s.synced = True


class TestOrchestrationOrder:
    def test_create(self):
        o = OrchestrationOrder("o1", "guardian", "start", 5)
        assert o.priority == 5

    def test_immutable(self):
        o = OrchestrationOrder("o", "g")
        with pytest.raises(FrozenInstanceError):
            o.priority = 3


class TestCoordinationResult:
    def test_success(self):
        r = CoordinationResult("r1", True, "ok")
        assert r.success

    def test_immutable(self):
        r = CoordinationResult("r")
        with pytest.raises(FrozenInstanceError):
            r.success = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestCoordinationEngine:
    def test_create_plan(self):
        e = CoordinationEngine()
        p = e.create_plan("p1")
        assert e.count() == 1

    def test_create_with_tasks(self):
        e = CoordinationEngine()
        tasks = [CoordinationTask("t1", "guardian", "boot"),
                 CoordinationTask("t2", "decision", "init")]
        p = e.create_plan("p1", tasks)
        assert p.total == 2

    def test_complete_task(self):
        e = CoordinationEngine()
        tasks = [CoordinationTask("t1", "guardian", "boot")]
        e.create_plan("p1", tasks)
        r = e.complete_task("p1", "t1")
        assert r.success
        p = e.get_plan("p1")
        assert p is not None
        assert p.completed == 1
        assert p.is_ready

    def test_complete_missing_plan(self):
        e = CoordinationEngine()
        r = e.complete_task("bogus", "t1")
        assert not r.success

    def test_complete_missing_task(self):
        e = CoordinationEngine()
        tasks = [CoordinationTask("t1", "guardian", "boot")]
        e.create_plan("p1", tasks)
        r = e.complete_task("p1", "bogus")
        assert not r.success

    def test_get_plan(self):
        e = CoordinationEngine()
        e.create_plan("p1")
        assert e.get_plan("p1") is not None
        assert e.get_plan("bogus") is None


class TestSyncCoordinator:
    def test_register(self):
        s = SyncCoordinator()
        s.register(SyncPoint("s1", "guardian"))
        assert s.count() == 1

    def test_get(self):
        s = SyncCoordinator()
        s.register(SyncPoint("s1", "guardian"))
        assert s.get("s1") is not None
        assert s.get("bogus") is None

    def test_mark_synced(self):
        s = SyncCoordinator()
        s.register(SyncPoint("s1", "guardian"))
        p = s.mark_synced("s1", "ok")
        assert p is not None
        assert p.synced

    def test_mark_missing(self):
        s = SyncCoordinator()
        p = s.mark_synced("bogus")
        assert p is None

    def test_list_unsynced(self):
        s = SyncCoordinator()
        s.register(SyncPoint("s1", "guardian"))
        s.register(SyncPoint("s2", "decision"))
        s.mark_synced("s1")
        assert len(s.list_unsynced()) == 1


class TestOrchestrator:
    def test_add(self):
        o = Orchestrator()
        o.add(OrchestrationOrder("o1", "guardian", "start", 1))
        assert o.count() == 1

    def test_get(self):
        o = Orchestrator()
        o.add(OrchestrationOrder("o1", "guardian", "start"))
        assert o.get("o1") is not None
        assert o.get("bogus") is None

    def test_execute_found(self):
        o = Orchestrator()
        o.add(OrchestrationOrder("o1", "guardian", "start"))
        r = o.execute("o1")
        assert r.success

    def test_execute_missing(self):
        o = Orchestrator()
        r = o.execute("bogus")
        assert not r.success

    def test_list_pending(self):
        o = Orchestrator()
        o.add(OrchestrationOrder("o1", "g", "start"))
        assert len(o.list_pending()) == 1


# ============================================================
# 3. Conversation Coordinator
# ============================================================

class TestConversationCoordinator:
    def test_queries(self):
        cc = ConversationCoordinator(CoordinationEngine(), SyncCoordinator(), Orchestrator())
        assert cc.get_engine() is not None
        assert cc.get_sync_coordinator() is not None
        assert cc.get_orchestrator() is not None
        layers = cc.describe_layers()
        assert len(layers) == 3
        assert cc.count_layers() == 3
        assert cc.get_plan_count() == 0
        assert cc.get_sync_count() == 0


# ============================================================
# 4. Dashboard Coordinator
# ============================================================

class TestDashboardCoordinator:
    def test_cards(self):
        dc = DashboardCoordinator(CoordinationEngine(), SyncCoordinator(), Orchestrator())
        for card in [dc.engine_card(), dc.plan_card(), dc.sync_card(),
                     dc.orcher_card(), dc.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        dc = DashboardCoordinator(CoordinationEngine(), SyncCoordinator(), Orchestrator())
        for card in [dc.engine_card(), dc.plan_card(), dc.sync_card(),
                     dc.orcher_card(), dc.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        CoordinationTask("t", "g"),
        CoordinationPlan("p"),
        SyncPoint("s", "g"),
        OrchestrationOrder("o", "g"),
        CoordinationResult("r"),
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

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_plan_parametrized(i):
    e = CoordinationEngine()
    tasks = [CoordinationTask(f"t{j}", f"sub{j}", "boot", "pending", j)
             for j in range(i % 6 + 1)]
    p = e.create_plan(f"p{i}", tasks)
    assert p.total == i % 6 + 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_sync_parametrized(i):
    s = SyncCoordinator()
    s.register(SyncPoint(f"s{i}", f"sub{i % 4}", False, f"data{i}"))
    assert s.count() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_orch_parametrized(i):
    o = Orchestrator()
    o.add(OrchestrationOrder(f"o{i}", f"sub{i % 3}", "start", i))
    assert o.count() == 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_complete_parametrized(i):
    e = CoordinationEngine()
    tasks = [CoordinationTask(f"t{j}", f"sub{j}", "boot", "pending", j)
             for j in range(i % 5 + 1)]
    e.create_plan("p1", tasks)
    for j in range(i % 5 + 1):
        r = e.complete_task("p1", f"t{j}")
        assert r.success
    p = e.get_plan("p1")
    assert p is not None
    assert p.is_ready


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cc = ConversationCoordinator(CoordinationEngine(), SyncCoordinator(), Orchestrator())
    assert cc.count_layers() == 3


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dc = DashboardCoordinator(CoordinationEngine(), SyncCoordinator(), Orchestrator())
    c = dc.engine_card()
    assert c.status == "ready"
