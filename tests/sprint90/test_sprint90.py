"""Sprint 90 — Execution Planning Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.execution_plan import ExecutionPlan
from sam.execution.runtime.execution_strategy import (
    ExecutionStrategy, SequenceBuilder, ExecutionPriority,
    ExecutionSchedule, StrategyResult, SequenceStep,
    ExecutionSequence, PriorityAssignment, ScheduleWindow,
)
from sam.execution.runtime.conversation_planning import ConversationPlanning
from sam.execution.runtime.dashboard_planning import DashboardPlanning
from sam.execution.runtime.dashboard_execution import ExecutionCard
from sam.execution.runtime.execution_builder import ExecutionBuilder


# ============================================================
# Helpers
# ============================================================

def make_candidates(count: int, type_: str = "immediate") -> list:
    return [
        ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                          candidate_type=type_)
        for i in range(count)
    ]

def make_candidates_with_deps(count: int) -> list:
    return [
        ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                          candidate_type="immediate",
                          dependencies=[f"c{j}" for j in range(i)])
        for i in range(count)
    ]


# ============================================================
# 1. ExecutionPlan DTO Tests
# ============================================================

class TestExecutionPlan:
    def test_create_minimal(self):
        plan = ExecutionPlan("p1", "d1", "e1", 5, 10)
        assert plan.plan_id == "p1"
        assert plan.draft_id == "d1"
        assert plan.context_id == "e1"
        assert plan.total_tasks == 5
        assert plan.total_steps == 10
        assert plan.environment == "normal"
        assert plan.strategies == []
        assert plan.sequences == []
        assert plan.priority_score == 0.0
        assert plan.schedule_info == {}

    def test_create_full(self):
        plan = ExecutionPlan(
            plan_id="p2", draft_id="d2", context_id="e2",
            total_tasks=10, total_steps=25,
            environment="critical",
            strategies=["sequential", "parallel"],
            sequences=["seq_1"],
            priority_score=0.85,
            schedule_info={"window": "w1"},
        )
        assert plan.environment == "critical"
        assert plan.strategies == ["sequential", "parallel"]
        assert plan.sequences == ["seq_1"]
        assert plan.priority_score == 0.85

    def test_immutable(self):
        plan = ExecutionPlan("p", "d", "e", 1, 1)
        with pytest.raises(FrozenInstanceError):
            plan.plan_id = "changed"


# ============================================================
# 2. ExecutionStrategy Tests
# ============================================================

class TestExecutionStrategy:
    def test_sequential(self):
        s = ExecutionStrategy()
        candidates = make_candidates(3)
        result = s.sequential(candidates)
        assert result.strategy_type == "sequential"
        assert len(result.candidate_ids) == 3

    def test_sequential_with_deps(self):
        s = ExecutionStrategy()
        candidates = make_candidates_with_deps(3)
        result = s.sequential(candidates)
        assert len(result.candidate_ids) == 3
        # no-deps candidates first
        assert result.score == 0.8

    def test_parallel(self):
        s = ExecutionStrategy()
        candidates = make_candidates(4)
        result = s.parallel(candidates)
        assert result.strategy_type == "parallel"
        assert len(result.candidate_ids) == 4

    def test_parallel_with_deps(self):
        s = ExecutionStrategy()
        candidates = make_candidates_with_deps(2)
        result = s.parallel(candidates)
        assert len(result.candidate_ids) == 2

    def test_prioritized(self):
        s = ExecutionStrategy()
        candidates = make_candidates(3)
        result = s.prioritized(candidates)
        assert result.strategy_type == "prioritized"
        assert result.score == 0.9

    def test_prioritized_empty(self):
        s = ExecutionStrategy()
        result = s.prioritized([])
        assert result.score == 0.0

    def test_conditional(self):
        s = ExecutionStrategy()
        candidates = [
            ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="conditional"),
            ExecutionCandidate("c2", "e1", "r1", 2.0, candidate_type="immediate"),
        ]
        result = s.conditional(candidates)
        assert result.strategy_type == "conditional"
        assert "c1" in result.candidate_ids

    def test_fallback(self):
        s = ExecutionStrategy()
        candidates = make_candidates(2)
        result = s.fallback(candidates)
        assert result.strategy_type == "fallback"
        assert result.score == 0.5

    def test_auto_select_immediate(self):
        s = ExecutionStrategy()
        candidates = make_candidates(2, "immediate")
        result = s.auto_select(candidates)
        assert result.strategy_type == "prioritized"

    def test_auto_select_scheduled(self):
        s = ExecutionStrategy()
        candidates = make_candidates(2, "scheduled")
        result = s.auto_select(candidates)
        assert result.strategy_type == "sequential"

    def test_auto_select_few(self):
        s = ExecutionStrategy()
        candidates = make_candidates(2, "batch")
        result = s.auto_select(candidates)
        assert result.strategy_type == "parallel"

    def test_auto_select_many(self):
        s = ExecutionStrategy()
        candidates = make_candidates(5, "batch")
        result = s.auto_select(candidates)
        assert result.strategy_type == "sequential"

    def test_strategy_result_frozen(self):
        r = StrategyResult("test", ["c1", "c2"])
        with pytest.raises(FrozenInstanceError):
            r.strategy_type = "changed"


# ============================================================
# 3. SequenceBuilder Tests
# ============================================================

class TestSequenceBuilder:
    def test_build_sequence(self):
        s = ExecutionStrategy()
        candidates = make_candidates(3)
        result = s.sequential(candidates)
        builder = SequenceBuilder()
        seq = builder.build(result, candidates)
        assert seq.sequence_id.startswith("seq_")
        assert seq.total_steps == 3
        assert len(seq.steps) == 3

    def test_build_with_deps(self):
        s = ExecutionStrategy()
        candidates = make_candidates_with_deps(3)
        result = s.sequential(candidates)
        builder = SequenceBuilder()
        seq = builder.build(result, candidates)
        assert seq.total_steps == 3

    def test_sequence_frozen(self):
        seq = ExecutionSequence("s1", [], 0)
        with pytest.raises(FrozenInstanceError):
            seq.sequence_id = "changed"

    def test_step_frozen(self):
        step = SequenceStep(1, "c1")
        with pytest.raises(FrozenInstanceError):
            step.step_id = 999


# ============================================================
# 4. ExecutionPriority Tests
# ============================================================

class TestExecutionPriority:
    def test_assign_single(self):
        p = ExecutionPriority()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=50.0)
        ass = p.assign(c)
        assert ass.candidate_id == "c1"
        assert 0.0 <= ass.priority_score <= 1.0
        assert "Effort-based" in ass.reason

    def test_assign_zero_effort(self):
        p = ExecutionPriority()
        c = ExecutionCandidate("c2", "e1", "r1", 1.0, estimated_effort=0.0)
        ass = p.assign(c)
        assert ass.priority_score == 1.0

    def test_assign_high_effort(self):
        p = ExecutionPriority()
        c = ExecutionCandidate("c3", "e1", "r1", 1.0, estimated_effort=200.0)
        ass = p.assign(c)
        assert ass.priority_score == 0.0

    def test_assign_all(self):
        p = ExecutionPriority()
        candidates = [
            ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 10))
            for i in range(5)
        ]
        results = p.assign_all(candidates)
        assert len(results) == 5
        # Assert ordered by priority desc
        for i in range(len(results) - 1):
            assert results[i].priority_score >= results[i + 1].priority_score

    def test_priority_assignment_frozen(self):
        a = PriorityAssignment("c1", 0.8)
        with pytest.raises(FrozenInstanceError):
            a.candidate_id = "changed"


# ============================================================
# 5. ExecutionSchedule Tests
# ============================================================

class TestExecutionSchedule:
    def test_create_window(self):
        s = ExecutionSchedule()
        candidates = make_candidates(2)
        w = s.create_window("w1", 100.0, 200.0, candidates)
        assert w.window_id == "w1"
        assert w.start_time == 100.0
        assert w.end_time == 200.0
        assert len(w.candidate_ids) == 2

    def test_window_empty_candidates(self):
        s = ExecutionSchedule()
        w = s.create_window("w2", 0.0, 100.0, [])
        assert w.candidate_ids == []

    def test_schedule_window_frozen(self):
        w = ScheduleWindow("w1", 0.0, 100.0, ["c1"])
        with pytest.raises(FrozenInstanceError):
            w.window_id = "changed"


# ============================================================
# 6. ConversationPlanning Tests
# ============================================================

class TestConversationPlanning:
    def test_queries(self):
        cp = ConversationPlanning(
            ExecutionStrategy(), SequenceBuilder(),
            ExecutionPriority(), ExecutionSchedule(),
        )
        assert cp.count_strategies() == 5
        strategies = cp.describe_strategies()
        assert len(strategies) == 5
        assert "sequential" in strategies
        pr = cp.get_priority_range()
        assert pr["min"] == 0.0
        assert pr["max"] == 1.0
        caps = cp.get_schedule_capabilities()
        assert "window_creation" in caps
        assert cp.get_strategy() is not None
        assert cp.get_sequence_builder() is not None
        assert cp.get_priority() is not None
        assert cp.get_schedule() is not None


# ============================================================
# 7. DashboardPlanning Tests
# ============================================================

class TestDashboardPlanning:
    def test_cards(self):
        dp = DashboardPlanning(
            ExecutionStrategy(), SequenceBuilder(),
            ExecutionPriority(), ExecutionSchedule(),
        )
        sc = dp.strategy_card()
        assert sc.status == "ready"
        assert sc.metrics["available_strategies"] == 5
        seqc = dp.sequence_card()
        assert seqc.metrics["builder_available"]
        pc = dp.priority_card()
        assert pc.metrics["range_min"] == 0.0
        schc = dp.schedule_card()
        assert schc.metrics["window_support"]
        sumc = dp.summary_card()
        assert sumc.metrics["strategies"] == 5

    def test_all_frozen(self):
        dp = DashboardPlanning(
            ExecutionStrategy(), SequenceBuilder(),
            ExecutionPriority(), ExecutionSchedule(),
        )
        for card in [dp.strategy_card(), dp.sequence_card(),
                     dp.priority_card(), dp.schedule_card(),
                     dp.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 8. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        ExecutionPlan("p", "d", "e", 1, 1),
        StrategyResult("s", []),
        SequenceStep(1, "c1"),
        ExecutionSequence("s", [], 0),
        PriorityAssignment("c", 0.5),
        ScheduleWindow("w", 0.0, 1.0),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 9. Forbidden Imports
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
# 10. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 21)))
def test_strategy_parametrized(i):
    s = ExecutionStrategy()
    c = make_candidates(i % 5 + 1)
    result = s.sequential(c)
    assert len(result.candidate_ids) == len(c)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_sequence_parametrized(i):
    s = ExecutionStrategy()
    c = make_candidates(i % 4 + 1)
    result = s.parallel(c)
    builder = SequenceBuilder()
    seq = builder.build(result, c)
    assert seq.total_steps >= 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_priority_parametrized(i):
    p = ExecutionPriority()
    candidates = [
        ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j * 5 + i))
        for j in range(i % 5 + 1)
    ]
    results = p.assign_all(candidates)
    assert len(results) == len(candidates)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_schedule_parametrized(i):
    s = ExecutionSchedule()
    candidates = make_candidates(i % 3 + 1)
    w = s.create_window(f"w{i}", float(i), float(i * 10), candidates)
    assert w.window_id == f"w{i}"


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_conversation_planning_parametrized(i):
    cp = ConversationPlanning(
        ExecutionStrategy(), SequenceBuilder(),
        ExecutionPriority(), ExecutionSchedule(),
    )
    assert cp.count_strategies() == 5
    assert len(cp.describe_strategies()) == 5


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_auto_select_parametrized(i):
    s = ExecutionStrategy()
    types = ["immediate", "scheduled", "conditional", "batch", "pipeline"]
    t = types[i % len(types)]
    candidates = make_candidates(i % 4 + 1, t)
    result = s.auto_select(candidates)
    assert result.strategy_type in ["sequential", "parallel", "prioritized"]


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_priority_score_values(i):
    p = ExecutionPriority()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 7))
    ass = p.assign(c)
    assert 0.0 <= ass.priority_score <= 1.0
