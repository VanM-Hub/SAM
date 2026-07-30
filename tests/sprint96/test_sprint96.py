"""Sprint 96 — Execution Budget/Cost Engine Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.budget import Budget, CostEstimate, BudgetReport, BudgetSummary
from sam.execution.runtime.budget_engine import BudgetEngine
from sam.execution.runtime.conversation_budget import ConversationBudget, DashboardBudget
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Budget DTO Tests
# ============================================================

class TestBudget:
    def test_create(self):
        b = Budget("b1", "ep1", total_budget=1000.0)
        assert b.budget_id == "b1"
        assert b.total_budget == 1000.0
        assert b.cpu_cost_rate == 1.0

    def test_immutable(self):
        b = Budget("b", "ep")
        with pytest.raises(FrozenInstanceError):
            b.total_budget = 999


class TestCostEstimate:
    def test_create(self):
        e = CostEstimate("e1", "c1", cpu_cost=10.0, memory_cost=5.0, estimated_total=15.0)
        assert e.estimate_id == "e1"
        assert e.candidate_id == "c1"
        assert e.estimated_total == 15.0

    def test_immutable(self):
        e = CostEstimate("e", "c")
        with pytest.raises(FrozenInstanceError):
            e.estimated_total = 999


class TestBudgetReport:
    def test_over_budget(self):
        r = BudgetReport("b1", total_allocated=100.0, total_estimated=150.0,
                        remaining=-50.0, is_over_budget=True, overage_amount=50.0)
        assert r.is_over_budget
        assert r.overage_amount == 50.0

    def test_immutable(self):
        r = BudgetReport("b")
        with pytest.raises(FrozenInstanceError):
            r.is_over_budget = True


class TestBudgetSummary:
    def test_defaults(self):
        s = BudgetSummary()
        assert s.status == "clean"
        assert s.total_budgets == 0

    def test_immutable(self):
        s = BudgetSummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "over_budget"


# ============================================================
# 2. BudgetEngine Tests
# ============================================================

class TestBudgetEngine:
    def test_register_budget(self):
        e = BudgetEngine()
        b = Budget("b1", "ep1", total_budget=500.0)
        e.register_budget(b)
        assert e.get_budget("b1") is not None

    def test_estimate(self):
        e = BudgetEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)
        est = e.estimate(c)
        assert est.candidate_id == "c1"
        assert est.cpu_cost > 0
        assert est.estimated_total > 0

    def test_estimate_routes(self):
        e = BudgetEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)
        est = e.estimate(c, cpu_rate=2.0, memory_rate=1.0, storage_rate=0.5, network_rate=0.1)
        assert est.cpu_cost == 40.0  # 10 * 2.0 * 2
        assert est.memory_cost == 100.0  # 10 * 1.0 * 10
        assert est.network_cost == 1.0

    def test_estimate_batch(self):
        e = BudgetEngine()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 5))
             for i in range(5)]
        estimates = e.estimate_batch(c)
        assert len(estimates) == 5

    def test_generate_report(self):
        e = BudgetEngine()
        b = Budget("b1", "ep1", total_budget=1000.0)
        e.register_budget(b)
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)
        e.estimate(c)
        r = e.generate_report("b1")
        assert r is not None
        assert r.total_allocated == 1000.0
        assert r.total_estimated > 0

    def test_generate_report_missing(self):
        e = BudgetEngine()
        r = e.generate_report("bogus")
        assert r is None

    def test_over_budget(self):
        e = BudgetEngine()
        b = Budget("b1", "ep1", total_budget=1.0)
        e.register_budget(b)
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=100.0)
        e.estimate(c)
        r = e.generate_report("b1")
        assert r is not None
        assert r.is_over_budget
        assert r.overage_amount > 0

    def test_summary_clean(self):
        e = BudgetEngine()
        s = e.get_summary()
        assert s.status == "clean"

    def test_summary_with_data(self):
        e = BudgetEngine()
        e.register_budget(Budget("b1", "ep1", total_budget=100.0))
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0)
        e.estimate(c)
        s = e.get_summary()
        assert s.total_budgets == 1
        assert s.total_estimated_cost > 0


# ============================================================
# 3. ConversationBudget Tests
# ============================================================

class TestConversationBudget:
    def test_queries(self):
        cb = ConversationBudget(BudgetEngine())
        assert cb.get_engine() is not None
        caps = cb.describe_capabilities()
        assert len(caps) >= 5
        assert cb.count_capabilities() >= 5
        types = cb.get_supported_cost_types()
        assert len(types) == 4
        assert cb.count_cost_types() == 4
        assert cb.count_budgets() == 0
        assert cb.count_estimates() == 0


# ============================================================
# 4. DashboardBudget Tests
# ============================================================

class TestDashboardBudget:
    def test_cards(self):
        db = DashboardBudget(BudgetEngine())
        ec = db.engine_card()
        assert ec.status == "ready"
        bc = db.budget_card()
        assert bc.status == "ready"
        estc = db.estimate_card()
        assert estc.status == "idle"
        rc = db.report_card()
        assert rc.status == "clean"
        sc = db.summary_card()
        assert sc.status == "clean"

    def test_cards_with_data(self):
        e = BudgetEngine()
        e.register_budget(Budget("b1", "ep1", total_budget=100.0))
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0)
        e.estimate(c)
        db = DashboardBudget(e)
        estc = db.estimate_card()
        assert estc.metrics["total_estimated"] > 0

    def test_all_frozen(self):
        db = DashboardBudget(BudgetEngine())
        for card in [db.engine_card(), db.budget_card(), db.estimate_card(),
                     db.report_card(), db.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [Budget("b", "ep"), CostEstimate("e", "c"),
                BudgetReport("b"), BudgetSummary()]:
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

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_estimate_parametrized(i):
    e = BudgetEngine()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 2))
    est = e.estimate(c)
    assert est.estimated_total > 0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_estimate_batch_parametrized(i):
    e = BudgetEngine()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j))
         for j in range(i % 8 + 1)]
    estimates = e.estimate_batch(c)
    assert len(estimates) == len(c)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_report_parametrized(i):
    e = BudgetEngine()
    e.register_budget(Budget(f"b{i}", "ep1", total_budget=float(i * 100)))
    c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(i))
    e.estimate(c)
    r = e.generate_report(f"b{i}")
    assert r is not None


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_summary_parametrized(i):
    e = BudgetEngine()
    for j in range(i % 5 + 1):
        e.register_budget(Budget(f"b{j}", "ep1", total_budget=100.0))
    s = e.get_summary()
    assert s.total_budgets == i % 5 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_budget_parametrized(i):
    e = BudgetEngine()
    for j in range(i):
        e.register_budget(Budget(f"b{j}", "ep1", total_budget=100.0))
    cb = ConversationBudget(e)
    assert cb.count_budgets() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_budget_parametrized(i):
    e = BudgetEngine()
    for j in range(i % 3):
        e.register_budget(Budget(f"b{j}", "ep1", total_budget=100.0))
    db = DashboardBudget(e)
    c = db.budget_card()
    assert c.metrics["total_budgets"] == i % 3


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_over_budget_parametrized(i):
    e = BudgetEngine()
    e.register_budget(Budget("b1", "ep1", total_budget=1.0))
    c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(i))
    e.estimate(c)
    r = e.generate_report("b1")
    assert r.is_over_budget
