"""Sprint 92 — Execution Dependencies Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.dependency_graph import (
    DependencyGraph, DependencyNode, DependencyValidation,
    ExecutionOrder, DependencySummary,
)
from sam.execution.runtime.dependency_resolver import (
    DependencyGraphBuilder, DependencyValidator, ExecutionOrderResolver,
)
from sam.execution.runtime.conversation_dependencies import (
    ConversationDependencies, DashboardDependencies,
)
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Dependency DTO Tests
# ============================================================

class TestDependencyNode:
    def test_create(self):
        n = DependencyNode("c1", depends_on=("c0",))
        assert n.candidate_id == "c1"
        assert n.depends_on == ("c0",)

    def test_empty(self):
        n = DependencyNode("c1")
        assert n.depends_on == ()

    def test_immutable(self):
        n = DependencyNode("c1")
        with pytest.raises(FrozenInstanceError):
            n.candidate_id = "changed"


class TestDependencyGraph:
    def test_empty(self):
        g = DependencyGraph()
        assert g.nodes == {}
        assert g.edges == 0
        assert g.levels == 0

    def test_with_nodes(self):
        n1 = DependencyNode("c1", depends_on=("c0",))
        n2 = DependencyNode("c2", depends_on=("c1",))
        g = DependencyGraph(nodes={"c1": n1, "c2": n2}, edges=2, levels=2)
        assert g.edges == 2
        assert g.levels == 2

    def test_immutable(self):
        g = DependencyGraph()
        with pytest.raises(FrozenInstanceError):
            g.edges = 5


class TestDependencyValidation:
    def test_valid(self):
        v = DependencyValidation(valid=True, total_dependencies=3)
        assert v.valid
        assert v.errors == []
        assert v.total_dependencies == 3

    def test_invalid(self):
        v = DependencyValidation(valid=False, errors=["missing: c1 -> c0"])
        assert not v.valid
        assert len(v.errors) == 1

    def test_immutable(self):
        v = DependencyValidation()
        with pytest.raises(FrozenInstanceError):
            v.valid = False


class TestExecutionOrder:
    def test_empty(self):
        o = ExecutionOrder("e1")
        assert o.ordered_candidate_ids == ()
        assert o.total_levels == 0

    def test_with_order(self):
        o = ExecutionOrder("e1", ordered_candidate_ids=("c1", "c2"), total_levels=1)
        assert len(o.ordered_candidate_ids) == 2
        assert o.total_levels == 1

    def test_immutable(self):
        o = ExecutionOrder("e1")
        with pytest.raises(FrozenInstanceError):
            o.order_id = "changed"


class TestDependencySummary:
    def test_defaults(self):
        s = DependencySummary()
        assert s.total_nodes == 0
        assert s.status == "empty"

    def test_custom(self):
        s = DependencySummary(total_nodes=5, total_edges=10, has_cycles=False, status="verified")
        assert s.total_nodes == 5
        assert s.status == "verified"

    def test_immutable(self):
        s = DependencySummary()
        with pytest.raises(FrozenInstanceError):
            s.total_nodes = 5


# ============================================================
# 2. DependencyGraphBuilder Tests
# ============================================================

class TestDependencyGraphBuilder:
    def test_build_empty(self):
        b = DependencyGraphBuilder()
        g = b.build([])
        assert g.nodes == {}
        assert g.edges == 0

    def test_build_no_deps(self):
        b = DependencyGraphBuilder()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i)) for i in range(3)]
        g = b.build(c)
        assert len(g.nodes) == 3
        assert g.edges == 0
        assert g.levels == 0

    def test_build_with_deps(self):
        b = DependencyGraphBuilder()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0),
            ExecutionCandidate("c1", "e1", "r1", 2.0, dependencies=["c0"]),
            ExecutionCandidate("c2", "e1", "r1", 3.0, dependencies=["c1"]),
        ]
        g = b.build(c)
        assert g.edges == 2
        assert g.levels >= 1

    def test_build_chain(self):
        b = DependencyGraphBuilder()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                               dependencies=[f"c{i-1}"] if i > 0 else [])
             for i in range(5)]
        g = b.build(c)
        assert g.edges == 4
        assert g.levels >= 3


# ============================================================
# 3. DependencyValidator Tests
# ============================================================

class TestDependencyValidator:
    def test_valid_no_deps(self):
        b = DependencyGraphBuilder()
        v = DependencyValidator()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i)) for i in range(3)]
        g = b.build(c)
        result = v.validate(g, c)
        assert result.valid
        assert result.errors == []

    def test_valid_with_deps(self):
        b = DependencyGraphBuilder()
        v = DependencyValidator()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0),
            ExecutionCandidate("c1", "e1", "r1", 2.0, dependencies=["c0"]),
        ]
        g = b.build(c)
        result = v.validate(g, c)
        assert result.valid

    def test_missing_dependency(self):
        b = DependencyGraphBuilder()
        v = DependencyValidator()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0, dependencies=["c_missing"]),
        ]
        g = b.build(c)
        result = v.validate(g, c)
        assert not result.valid
        assert len(result.errors) == 1
        assert "Missing" in result.errors[0]

    def test_potential_cycle_warning(self):
        # Manual graph — tidak via builder (builder akan stack overflow)
        from sam.execution.runtime.dependency_graph import DependencyGraph
        n0 = DependencyNode("c0", depends_on=("c1",))
        n1 = DependencyNode("c1", depends_on=("c0",))
        g = DependencyGraph(nodes={"c0": n0, "c1": n1}, edges=2, levels=1)
        v = DependencyValidator()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0, dependencies=["c1"]),
            ExecutionCandidate("c1", "e1", "r1", 2.0, dependencies=["c0"]),
        ]
        result = v.validate(g, c)
        assert result.warnings


# ============================================================
# 4. ExecutionOrderResolver Tests
# ============================================================

class TestExecutionOrderResolver:
    def test_resolve_no_deps(self):
        b = DependencyGraphBuilder()
        r = ExecutionOrderResolver()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i)) for i in range(3)]
        g = b.build(c)
        order = r.resolve(g, c)
        assert not order.has_cycles
        assert len(order.ordered_candidate_ids) == 3

    def test_resolve_with_deps(self):
        b = DependencyGraphBuilder()
        r = ExecutionOrderResolver()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0),
            ExecutionCandidate("c1", "e1", "r1", 2.0, dependencies=["c0"]),
            ExecutionCandidate("c2", "e1", "r1", 3.0, dependencies=["c1"]),
        ]
        g = b.build(c)
        order = r.resolve(g, c)
        assert not order.has_cycles
        # c0 should be before c1 before c2
        ids = list(order.ordered_candidate_ids)
        assert ids.index("c0") < ids.index("c1")
        assert ids.index("c1") < ids.index("c2")

    def test_resolve_levels(self):
        b = DependencyGraphBuilder()
        r = ExecutionOrderResolver()
        c = [
            ExecutionCandidate("c0", "e1", "r1", 1.0),
            ExecutionCandidate("c1", "e1", "r1", 2.0, dependencies=["c0"]),
        ]
        g = b.build(c)
        order = r.resolve(g, c)
        assert order.total_levels >= 1

    def test_get_summary(self):
        b = DependencyGraphBuilder()
        r = ExecutionOrderResolver()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i)) for i in range(3)]
        g = b.build(c)
        order = r.resolve(g, c)
        summary = r.get_summary(g, order)
        assert summary.total_nodes == 3
        assert summary.status == "verified"


# ============================================================
# 5. ConversationDependencies Tests
# ============================================================

class TestConversationDependencies:
    def test_queries(self):
        cd = ConversationDependencies(
            DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
        )
        assert cd.get_graph_builder() is not None
        assert cd.get_validator() is not None
        assert cd.get_resolver() is not None
        caps = cd.describe_capabilities()
        assert len(caps) == 5
        assert cd.count_graph_capabilities() == 5

    def test_graph_queries(self):
        cd = ConversationDependencies(
            DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
        )
        c = [ExecutionCandidate("c0", "e1", "r1", 1.0)]
        g = DependencyGraphBuilder().build(c)
        assert cd.get_max_depth(g) >= 0
        assert cd.count_dependencies(g) >= 0


# ============================================================
# 6. DashboardDependencies Tests
# ============================================================

class TestDashboardDependencies:
    def test_cards(self):
        dd = DashboardDependencies(
            DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
        )
        gc = dd.graph_card()
        assert gc.status == "ready"
        vc = dd.validation_card()
        assert vc.metrics["cycle_detection"]
        oc = dd.order_card()
        assert oc.metrics["resolver_ready"]
        sc = dd.summary_card()
        assert sc.metrics["capabilities"] == 5
        stc = dd.status_card()
        assert stc.status == "active"

    def test_all_frozen(self):
        dd = DashboardDependencies(
            DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
        )
        for card in [dd.graph_card(), dd.validation_card(), dd.order_card(),
                     dd.summary_card(), dd.status_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 7. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        DependencyNode("c1"), DependencyGraph(),
        DependencyValidation(), ExecutionOrder("e1"), DependencySummary(),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 8. Forbidden Imports
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
# 9. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 26)))
def test_graph_builder_parametrized(i):
    b = DependencyGraphBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                           dependencies=[f"c{j-1}"] if j > 0 else [])
         for j in range(i % 5 + 1)]
    g = b.build(c)
    assert len(g.nodes) == len(c)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_validator_parametrized(i):
    v = DependencyValidator()
    b = DependencyGraphBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j)) for j in range(i % 5 + 1)]
    g = b.build(c)
    result = v.validate(g, c)
    assert isinstance(result, DependencyValidation)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_resolver_parametrized(i):
    r = ExecutionOrderResolver()
    b = DependencyGraphBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j)) for j in range(i % 6 + 1)]
    g = b.build(c)
    order = r.resolve(g, c)
    assert isinstance(order, ExecutionOrder)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_resolver_with_deps_parametrized(i):
    r = ExecutionOrderResolver()
    b = DependencyGraphBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                           dependencies=[f"c{j-1}"] if j > 0 and j < i else [])
         for j in range(i % 4 + 1)]
    g = b.build(c)
    order = r.resolve(g, c)
    assert len(order.ordered_candidate_ids) == len(c)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_summary_parametrized(i):
    r = ExecutionOrderResolver()
    b = DependencyGraphBuilder()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j)) for j in range(i)]
    g = b.build(c)
    order = r.resolve(g, c)
    summary = r.get_summary(g, order)
    assert summary.total_nodes == i


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_deps_parametrized(i):
    cd = ConversationDependencies(
        DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
    )
    assert cd.count_graph_capabilities() == 5


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_deps_parametrized(i):
    dd = DashboardDependencies(
        DependencyGraphBuilder(), DependencyValidator(), ExecutionOrderResolver(),
    )
    c = dd.graph_card()
    assert c.status == "ready"
