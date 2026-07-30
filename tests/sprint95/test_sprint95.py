"""Sprint 95 — Execution Simulation Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.simulation import (
    SimulationConfig, SimulationStep, SimulationResult, SimulationSummary,
)
from sam.execution.runtime.simulation_engine import SimulationEngine
from sam.execution.runtime.conversation_simulation import ConversationSimulation, DashboardSimulation
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Simulation DTO Tests
# ============================================================

class TestSimulationConfig:
    def test_create(self):
        c = SimulationConfig("sim1", "load_test", max_iterations=50, time_step_ms=5.0)
        assert c.simulation_id == "sim1"
        assert c.scenario_name == "load_test"
        assert c.max_iterations == 50
        assert c.time_step_ms == 5.0

    def test_immutable(self):
        c = SimulationConfig("s", "n")
        with pytest.raises(FrozenInstanceError):
            c.max_iterations = 999


class TestSimulationStep:
    def test_create(self):
        s = SimulationStep(1, 0.0, candidate_id="c1", action="execute",
                          cpu_used=2.0, memory_used=128.0, duration_ms=500.0)
        assert s.step_number == 1
        assert s.candidate_id == "c1"
        assert s.action == "execute"
        assert s.cpu_used == 2.0

    def test_immutable(self):
        s = SimulationStep(0, 0.0)
        with pytest.raises(FrozenInstanceError):
            s.step_number = 999


class TestSimulationResult:
    def test_empty(self):
        r = SimulationResult("sim1")
        assert r.total_steps == 0
        assert r.total_duration_ms == 0.0

    def test_full(self):
        steps = (SimulationStep(1, 0.0, "c1"), SimulationStep(2, 10.0, "c2"))
        r = SimulationResult("sim1", steps=steps, total_steps=2,
                           total_duration_ms=10000.0)
        assert r.total_steps == 2
        assert r.total_duration_ms == 10000.0

    def test_immutable(self):
        r = SimulationResult("s")
        with pytest.raises(FrozenInstanceError):
            r.total_steps = 5


class TestSimulationSummary:
    def test_defaults(self):
        s = SimulationSummary()
        assert s.status == "idle"
        assert s.total_simulations == 0

    def test_active(self):
        s = SimulationSummary(total_simulations=3, status="active")
        assert s.total_simulations == 3

    def test_immutable(self):
        s = SimulationSummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "active"


# ============================================================
# 2. SimulationEngine Tests
# ============================================================

class TestSimulationEngine:
    def test_simulate_empty(self):
        e = SimulationEngine()
        config = SimulationConfig("sim1", "test")
        r = e.simulate(config, [])
        assert r.total_steps == 0
        assert r.total_duration_ms == 0.0

    def test_simulate_with_candidates(self):
        e = SimulationEngine()
        config = SimulationConfig("sim1", "load_test", time_step_ms=10.0)
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0),
             ExecutionCandidate("c2", "e1", "r1", 2.0, estimated_effort=10.0)]
        r = e.simulate(config, c)
        assert r.total_steps == 2
        assert r.total_cpu_used > 0
        assert r.total_memory_used > 0
        assert r.total_duration_ms == 15000.0

    def test_simulate_steps(self):
        e = SimulationEngine()
        config = SimulationConfig("sim1", "test")
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0)]
        r = e.simulate(config, c)
        assert r.steps[0].step_number == 1
        assert r.steps[0].cpu_used == 10.0
        assert r.steps[0].memory_used == 50.0
        assert r.steps[0].duration_ms == 5000.0

    def test_simulate_batch(self):
        e = SimulationEngine()
        config = SimulationConfig("sim1", "batch_test")
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0,
                               candidate_type="batch")]
        r = e.simulate(config, c)
        assert r.steps[0].action == "batch"

    def test_multiple_simulations(self):
        e = SimulationEngine()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=1.0)]
        for i in range(3):
            e.simulate(SimulationConfig(f"sim{i}", "test"), c)
        summary = e.get_summary()
        assert summary.total_simulations == 3
        assert summary.avg_duration_ms > 0
        assert summary.status == "active"


# ============================================================
# 3. ConversationSimulation Tests
# ============================================================

class TestConversationSimulation:
    def test_queries(self):
        cs = ConversationSimulation(SimulationEngine())
        assert cs.get_engine() is not None
        caps = cs.describe_capabilities()
        assert len(caps) >= 4
        assert cs.count_capabilities() >= 4
        actions = cs.get_supported_actions()
        assert "execute" in actions
        assert cs.count_simulations() == 0


# ============================================================
# 4. DashboardSimulation Tests
# ============================================================

class TestDashboardSimulation:
    def test_cards(self):
        ds = DashboardSimulation(SimulationEngine())
        ec = ds.engine_card()
        assert ec.status == "ready"
        rc = ds.run_card()
        assert rc.status == "ready"
        resc = ds.results_card()
        assert resc.status == "idle"
        sc = ds.steps_card()
        assert sc.status == "idle"
        sumc = ds.summary_card()
        assert sumc.status == "idle"

    def test_results_card_with_data(self):
        e = SimulationEngine()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0)]
        e.simulate(SimulationConfig("sim1", "test"), c)
        ds = DashboardSimulation(e)
        resc = ds.results_card()
        assert resc.metrics["total_runs"] == 1

    def test_all_frozen(self):
        ds = DashboardSimulation(SimulationEngine())
        for card in [ds.engine_card(), ds.run_card(), ds.results_card(),
                     ds.steps_card(), ds.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        SimulationConfig("s", "n"),
        SimulationStep(0, 0.0),
        SimulationResult("s"),
        SimulationSummary(),
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
def test_simulate_parametrized(i):
    e = SimulationEngine()
    config = SimulationConfig(f"sim{i}", f"scenario_{i}")
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                           estimated_effort=float(j * 2))
         for j in range(i % 5 + 1)]
    r = e.simulate(config, c)
    assert r.total_steps == len(c)
    assert r.simulation_id == f"sim{i}"


@pytest.mark.parametrize("i", list(range(1, 26)))
def test_result_metrics_parametrized(i):
    e = SimulationEngine()
    c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(i))]
    r = e.simulate(SimulationConfig(f"sim{i}", "test"), c)
    assert r.total_duration_ms == float(i) * 1000.0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_summary_parametrized(i):
    e = SimulationEngine()
    c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=1.0)]
    for j in range(i % 5 + 1):
        e.simulate(SimulationConfig(f"sim{j}", "test"), c)
    s = e.get_summary()
    assert s.total_simulations == i % 5 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_simulation_parametrized(i):
    e = SimulationEngine()
    c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=1.0)]
    for j in range(i):
        e.simulate(SimulationConfig(f"sim{j}", "test"), c)
    cs = ConversationSimulation(e)
    assert cs.count_simulations() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_simulation_parametrized(i):
    e = SimulationEngine()
    for j in range(i % 4):
        c = [ExecutionCandidate(f"c{j}", "e1", "r1", 1.0, estimated_effort=1.0)]
        e.simulate(SimulationConfig(f"sim{j}", "test"), c)
    ds = DashboardSimulation(e)
    c = ds.results_card()
    assert c.metrics["total_runs"] == i % 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_step_fields_parametrized(i):
    e = SimulationEngine()
    c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(i))]
    r = e.simulate(SimulationConfig(f"sim{i}", "test"), c)
    if r.steps:
        assert r.steps[0].cpu_used == float(i) * 2.0
