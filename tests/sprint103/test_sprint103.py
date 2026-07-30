"""Sprint 103 — Runtime Lifecycle Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_lifecycle import (
    LifecyclePhase, StartupPlan, ShutdownPlan, RestartPlan,
)
from sam.runtime_kernel.lifecycle_manager import LifecycleManager
from sam.runtime_kernel.startup_manager import StartupManager
from sam.runtime_kernel.shutdown_manager import ShutdownManager
from sam.runtime_kernel.restart_manager import RestartManager
from sam.runtime_kernel.conversation_lifecycle import ConversationLifecycle, DashboardLifecycle
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestLifecyclePhase:
    def test_create(self):
        p = LifecyclePhase("p1", "booting", "pending", 1)
        assert p.name == "booting"

    def test_immutable(self):
        p = LifecyclePhase("p", "n")
        with pytest.raises(FrozenInstanceError):
            p.status = "completed"


class TestStartupPlan:
    def test_create(self):
        p = StartupPlan("sp1", total_phases=3, completed_phases=0)
        assert not p.is_ready

    def test_ready(self):
        p = StartupPlan("sp1", total_phases=3, completed_phases=3, is_ready=True)
        assert p.is_ready

    def test_immutable(self):
        p = StartupPlan("sp")
        with pytest.raises(FrozenInstanceError):
            p.is_ready = True


class TestShutdownPlan:
    def test_create(self):
        p = ShutdownPlan("sd1", "maintenance", True, total_tasks=4)
        assert p.reason == "maintenance"

    def test_complete(self):
        p = ShutdownPlan("sd1", is_complete=True)
        assert p.is_complete

    def test_immutable(self):
        p = ShutdownPlan("sd")
        with pytest.raises(FrozenInstanceError):
            p.is_complete = True


class TestRestartPlan:
    def test_create(self):
        p = RestartPlan("rp1", "sd1", "sp1")
        assert p.status == "pending"

    def test_immutable(self):
        p = RestartPlan("rp", "s", "sp")
        with pytest.raises(FrozenInstanceError):
            p.status = "completed"


# ============================================================
# 2. Engine Tests
# ============================================================

class TestLifecycleManager:
    def test_create_startup(self):
        m = LifecycleManager()
        p = m.create_startup("sp1")
        assert p.total_phases == 0
        assert m.count_startups() == 1

    def test_startup_with_phases(self):
        m = LifecycleManager()
        phases = [LifecyclePhase("p1", "context", "pending", 1),
                  LifecyclePhase("p2", "registry", "pending", 2)]
        p = m.create_startup("sp1", phases)
        assert p.total_phases == 2
        assert not p.is_ready

    def test_complete_startup_phase(self):
        m = LifecycleManager()
        phases = [LifecyclePhase("p1", "context", "pending", 1)]
        m.create_startup("sp1", phases)
        p = m.complete_startup_phase("sp1", "p1")
        assert p is not None
        assert p.completed_phases == 1
        assert p.is_ready

    def test_complete_startup_missing(self):
        m = LifecycleManager()
        r = m.complete_startup_phase("bogus", "p1")
        assert r is None

    def test_create_shutdown(self):
        m = LifecycleManager()
        p = m.create_shutdown("sd1", "shutdown", True)
        assert m.count_shutdowns() == 1
        assert not p.is_complete

    def test_mark_shutdown_complete(self):
        m = LifecycleManager()
        m.create_shutdown("sd1")
        p = m.mark_shutdown_complete("sd1")
        assert p is not None
        assert p.is_complete

    def test_create_restart(self):
        m = LifecycleManager()
        p = m.create_restart("rp1", "sd1", "sp1")
        assert m.count_restarts() == 1

    def test_complete_restart(self):
        m = LifecycleManager()
        m.create_restart("rp1", "sd1", "sp1")
        p = m.complete_restart("rp1")
        assert p is not None
        assert p.status == "completed"

    def test_getters(self):
        m = LifecycleManager()
        m.create_startup("sp1")
        m.create_shutdown("sd1")
        m.create_restart("rp1", "sd1", "sp1")
        assert m.get_startup("sp1") is not None
        assert m.get_shutdown("sd1") is not None
        assert m.get_restart("rp1") is not None
        assert m.get_startup("bogus") is None


class TestStartupManager:
    def test_build_plan(self):
        sm = StartupManager()
        phases = sm.build_plan()
        assert len(phases) == 6

    def test_count(self):
        sm = StartupManager()
        assert sm.count_phases() == 6

    def test_names(self):
        sm = StartupManager()
        names = sm.get_phase_names()
        assert "context" in names
        assert "engine" in names


class TestShutdownManager:
    def test_create_plan(self):
        sm = ShutdownManager()
        p = sm.create_plan("sd1", "maintenance")
        assert p.total_tasks == 4

    def test_list_tasks(self):
        sm = ShutdownManager()
        assert len(sm.list_tasks()) == 4

    def test_count(self):
        sm = ShutdownManager()
        assert sm.count_tasks() == 4


class TestRestartManager:
    def test_create_plan(self):
        rm = RestartManager()
        p = rm.create_plan("rp1", "sd1", "sp1")
        assert p.status == "pending"

    def test_complete_plan(self):
        rm = RestartManager()
        p = rm.create_plan("rp1", "sd1", "sp1")
        p2 = rm.complete_plan(p)
        assert p2.status == "completed"


# ============================================================
# 3. Conversation Lifecycle
# ============================================================

class TestConversationLifecycle:
    def test_queries(self):
        cl = ConversationLifecycle(LifecycleManager(), StartupManager(),
                                   ShutdownManager(), RestartManager())
        assert cl.get_lifecycle_manager() is not None
        assert cl.get_startup_manager() is not None
        assert cl.get_shutdown_manager() is not None
        assert cl.get_restart_manager() is not None
        phases = cl.describe_phases()
        assert len(phases) == 3
        assert cl.count_phases() == 3
        sp = cl.get_startup_phases()
        assert len(sp) == 6
        assert cl.count_startup_phases() == 6


# ============================================================
# 4. Dashboard Lifecycle
# ============================================================

class TestDashboardLifecycle:
    def test_cards(self):
        dl = DashboardLifecycle(LifecycleManager(), StartupManager())
        for card in [dl.engine_card(), dl.startup_card(), dl.shutdown_card(),
                     dl.restart_card(), dl.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        dl = DashboardLifecycle(LifecycleManager(), StartupManager())
        for card in [dl.engine_card(), dl.startup_card(), dl.shutdown_card(),
                     dl.restart_card(), dl.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        LifecyclePhase("p", "n"),
        StartupPlan("sp"),
        ShutdownPlan("sd"),
        RestartPlan("rp", "sd", "sp"),
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
def test_startup_parametrized(i):
    m = LifecycleManager()
    phases = [LifecyclePhase(f"p{j}", f"phase{j}", "pending", j)
              for j in range(i % 6 + 1)]
    p = m.create_startup(f"sp{i}", phases)
    assert p.total_phases == i % 6 + 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_shutdown_parametrized(i):
    m = LifecycleManager()
    p = m.create_shutdown(f"sd{i}", f"Reason {i}", i % 2 == 0)
    assert p.graceful == (i % 2 == 0)


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_restart_parametrized(i):
    m = LifecycleManager()
    p = m.create_restart(f"rp{i}", f"sd{i}", f"sp{i}")
    assert p.status == "pending"


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_phase_complete_parametrized(i):
    m = LifecycleManager()
    phases = [LifecyclePhase(f"p{j}", f"Phase {j}", "pending", j)
              for j in range(i % 4 + 1)]
    m.create_startup("sp1", phases)
    for j in range(i % 4 + 1):
        m.complete_startup_phase("sp1", f"p{j}")
    p = m.get_startup("sp1")
    assert p is not None
    assert p.completed_phases == i % 4 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cl = ConversationLifecycle(LifecycleManager(), StartupManager(),
                               ShutdownManager(), RestartManager())
    assert cl.count_startup_phases() == 6


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dl = DashboardLifecycle(LifecycleManager(), StartupManager())
    c = dl.engine_card()
    assert c.status == "ready"
