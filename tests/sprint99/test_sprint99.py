"""Sprint 99 — Execution Plan Assembly Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.assembly import (
    AssemblyComponent, ExecutionAssembly, ReadinessReport, AssemblySummary,
)
from sam.execution.runtime.assembly_engine import AssemblyEngine
from sam.execution.runtime.conversation_assembly import ConversationAssembly, DashboardAssembly
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Assembly DTO Tests
# ============================================================

class TestAssemblyComponent:
    def test_create(self):
        c = AssemblyComponent("plan", "execution_plan", "ready",
                              description="Execution plan", items_count=5)
        assert c.name == "plan"
        assert c.status == "ready"
        assert c.items_count == 5

    def test_immutable(self):
        c = AssemblyComponent("n", "t", "s")
        with pytest.raises(FrozenInstanceError):
            c.status = "ready"


class TestExecutionAssembly:
    def test_create_ready(self):
        c = [AssemblyComponent("plan", "execution_plan", "ready")]
        a = ExecutionAssembly("a1", "ep1", components=tuple(c),
                            total_components=1, ready_components=1, is_ready=True)
        assert a.assembly_id == "a1"
        assert a.is_ready

    def test_not_ready(self):
        a = ExecutionAssembly("a1", "ep1", total_components=1, ready_components=0)
        assert not a.is_ready

    def test_immutable(self):
        a = ExecutionAssembly("a", "ep")
        with pytest.raises(FrozenInstanceError):
            a.is_ready = True


class TestReadinessReport:
    def test_ready(self):
        r = ReadinessReport("r1", "a1", overall_readiness=1.0,
                          component_readiness={"plan": 1.0}, is_ready=True)
        assert r.is_ready
        assert r.overall_readiness == 1.0

    def test_immutable(self):
        r = ReadinessReport("r", "a")
        with pytest.raises(FrozenInstanceError):
            r.is_ready = True


class TestAssemblySummary:
    def test_defaults(self):
        s = AssemblySummary()
        assert s.status == "not_ready"

    def test_ready(self):
        s = AssemblySummary(total_assemblies=1, ready_assemblies=1, status="ready")
        assert s.ready_assemblies == 1
        assert s.status == "ready"

    def test_immutable(self):
        s = AssemblySummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "ready"


# ============================================================
# 2. AssemblyEngine Tests
# ============================================================

class TestAssemblyEngine:
    def test_assemble_empty(self):
        e = AssemblyEngine()
        a = e.assemble("a1", "ep1")
        assert a.total_components == 0
        assert not a.is_ready

    def test_assemble_all_ready(self):
        e = AssemblyEngine()
        comps = [
            AssemblyComponent("plan", "execution_plan", "ready"),
            AssemblyComponent("resources", "resource_plan", "ready"),
            AssemblyComponent("deps", "dependency", "ready"),
        ]
        a = e.assemble("a1", "ep1", comps)
        assert a.total_components == 3
        assert a.ready_components == 3
        assert a.is_ready

    def test_assemble_mixed(self):
        e = AssemblyEngine()
        comps = [
            AssemblyComponent("plan", "execution_plan", "ready"),
            AssemblyComponent("failed", "resource", "failed"),
        ]
        a = e.assemble("a1", "ep1", comps)
        assert a.ready_components == 1
        assert a.failed_components == 1
        assert not a.is_ready

    def test_generate_report(self):
        e = AssemblyEngine()
        comps = [AssemblyComponent("plan", "execution_plan", "ready")]
        e.assemble("a1", "ep1", comps)
        r = e.generate_report("r1", "a1")
        assert r is not None
        assert r.overall_readiness == 1.0
        assert r.is_ready

    def test_generate_report_missing(self):
        e = AssemblyEngine()
        r = e.generate_report("r1", "bogus")
        assert r is None

    def test_generate_report_partial(self):
        e = AssemblyEngine()
        comps = [
            AssemblyComponent("plan", "execution_plan", "ready"),
            AssemblyComponent("deps", "dependency", "pending"),
            AssemblyComponent("risk", "risk_report", "failed"),
        ]
        e.assemble("a1", "ep1", comps)
        r = e.generate_report("r1", "a1")
        assert r is not None
        assert not r.is_ready
        assert r.overall_readiness < 1.0
        assert len(r.missing_components) >= 1

    def test_summary_empty(self):
        e = AssemblyEngine()
        s = e.get_summary()
        assert s.total_assemblies == 0
        assert s.status == "not_ready"

    def test_summary_with_data(self):
        e = AssemblyEngine()
        comps = [AssemblyComponent("plan", "execution_plan", "ready")]
        e.assemble("a1", "ep1", comps)
        s = e.get_summary()
        assert s.total_assemblies == 1

    def test_summary_ready(self):
        e = AssemblyEngine()
        comps = [AssemblyComponent("plan", "execution_plan", "ready")]
        e.assemble("a1", "ep1", comps)
        e.generate_report("r1", "a1")
        s = e.get_summary()
        assert s.ready_assemblies == 1
        assert s.status == "ready"

    def test_summary_partial(self):
        e = AssemblyEngine()
        comps = [AssemblyComponent("plan", "execution_plan", "failed")]
        e.assemble("a1", "ep1", comps)
        s = e.get_summary()
        assert s.status == "partial"  # ada assembly tapi ada yang gagal


# ============================================================
# 3. ConversationAssembly Tests
# ============================================================

class TestConversationAssembly:
    def test_queries(self):
        ca = ConversationAssembly(AssemblyEngine())
        assert ca.get_engine() is not None
        types = ca.get_component_types()
        assert len(types) == 7
        caps = ca.describe_capabilities()
        assert len(caps) >= 4
        assert ca.count_capabilities() >= 4
        assert ca.count_component_types() == 7


# ============================================================
# 4. DashboardAssembly Tests
# ============================================================

class TestDashboardAssembly:
    def test_cards(self):
        da = DashboardAssembly(AssemblyEngine())
        ec = da.engine_card()
        assert ec.status == "ready"
        ac = da.assembly_card()
        assert ac.status == "not_ready"
        rc = da.readiness_card()
        assert rc.status == "not_ready"
        repc = da.report_card()
        assert repc.status == "not_ready"
        sc = da.summary_card()
        assert sc.status == "not_ready"

    def test_cards_with_data(self):
        e = AssemblyEngine()
        comps = [AssemblyComponent("plan", "execution_plan", "ready")]
        e.assemble("a1", "ep1", comps)
        da = DashboardAssembly(e)
        ac = da.assembly_card()
        assert ac.metrics["total"] == 1

    def test_all_frozen(self):
        da = DashboardAssembly(AssemblyEngine())
        for card in [da.engine_card(), da.assembly_card(), da.readiness_card(),
                     da.report_card(), da.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        AssemblyComponent("n", "t", "s"),
        ExecutionAssembly("a", "ep"),
        ReadinessReport("r", "a"),
        AssemblySummary(),
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

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_assemble_parametrized(i):
    e = AssemblyEngine()
    comps = [AssemblyComponent(f"c{j}", "execution_plan", "ready" if j % 2 == 0 else "pending")
             for j in range(i % 6 + 1)]
    a = e.assemble(f"a{i}", "ep1", comps)
    assert a.total_components == len(comps)


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_report_parametrized(i):
    e = AssemblyEngine()
    comps = [AssemblyComponent("plan", "execution_plan", "ready")
             for _ in range(i % 4 + 1)]
    a_id = f"a{i}"
    e.assemble(a_id, "ep1", comps)
    r = e.generate_report(f"r{i}", a_id)
    assert r is not None
    assert r.overall_readiness >= 0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_summary_parametrized(i):
    e = AssemblyEngine()
    for j in range(i % 5 + 1):
        comps = [AssemblyComponent(f"c{j}", "execution_plan", "ready")]
        e.assemble(f"a{j}", "ep1", comps)
    s = e.get_summary()
    assert s.total_assemblies == i % 5 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_assembly_parametrized(i):
    e = AssemblyEngine()
    for j in range(i):
        e.assemble(f"a{j}", "ep1", [AssemblyComponent("plan", "execution_plan", "ready")])
    ca = ConversationAssembly(e)
    assert ca.count_assemblies() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_assembly_parametrized(i):
    e = AssemblyEngine()
    for j in range(i % 4):
        e.assemble(f"a{j}", "ep1", [AssemblyComponent("plan", "execution_plan", "ready")])
    da = DashboardAssembly(e)
    c = da.assembly_card()
    assert c.metrics["total"] == i % 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_not_ready_parametrized(i):
    e = AssemblyEngine()
    comps = [AssemblyComponent("plan", "execution_plan", "pending")]
    e.assemble(f"a{i}", "ep1", comps)
    r = e.generate_report(f"r{i}", f"a{i}")
    assert r is not None
    assert not r.is_ready
