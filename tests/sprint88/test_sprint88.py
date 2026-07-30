"""Sprint 88 — Execution Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.execution_registry import ExecutionRegistry, ExecutionSnapshot
from sam.execution.runtime.execution_builder import ExecutionBuilder
from sam.execution.runtime.runtime import ExecutionRuntime, ExecutionDraft
from sam.execution.runtime.conversation_execution import ConversationExecution
from sam.execution.runtime.dashboard_execution import DashboardExecution, ExecutionCard


# ============================================================
# 1. ExecutionContext Tests
# ============================================================

class TestExecutionContext:
    def test_create_minimal(self):
        ctx = ExecutionContext("e1", 1000.0)
        assert ctx.context_id == "e1"
        assert ctx.timestamp == 1000.0
        assert ctx.environment == "normal"
        assert ctx.total_tasks == 0
        assert ctx.total_steps == 0
        assert ctx.decision_id is None
        assert ctx.approval_id is None
        assert ctx.metadata == {}
        assert ctx.source_activation == ""

    def test_create_full(self):
        ctx = ExecutionContext(
            context_id="e2", timestamp=2000.0,
            source_activation="act_1", environment="critical",
            total_tasks=5, total_steps=20,
            decision_id="d1", approval_id="a1",
            metadata={"key": "val"},
        )
        assert ctx.context_id == "e2"
        assert ctx.source_activation == "act_1"
        assert ctx.environment == "critical"
        assert ctx.total_tasks == 5
        assert ctx.total_steps == 20
        assert ctx.decision_id == "d1"
        assert ctx.approval_id == "a1"
        assert ctx.metadata == {"key": "val"}

    def test_immutable(self):
        ctx = ExecutionContext("e3", 3000.0)
        with pytest.raises(FrozenInstanceError):
            ctx.context_id = "changed"

    def test_defaults(self):
        ctx = ExecutionContext("e4", 4000.0)
        assert ctx.source_activation == ""
        assert ctx.environment == "normal"
        assert ctx.total_tasks == 0
        assert ctx.total_steps == 0
        assert ctx.decision_id is None
        assert ctx.approval_id is None

    def test_environments(self):
        for env in ["normal", "restricted", "critical"]:
            ctx = ExecutionContext("e", 1.0, environment=env)
            assert ctx.environment == env


# ============================================================
# 2. ExecutionRequest Tests
# ============================================================

class TestExecutionRequest:
    def test_create_minimal(self):
        req = ExecutionRequest("r1", "e1", 1000.0)
        assert req.request_id == "r1"
        assert req.context_id == "e1"
        assert req.timestamp == 1000.0
        assert req.task_type == "process"
        assert req.priority == 5
        assert req.payload == {}
        assert req.tags == []
        assert req.metadata == {}

    def test_create_full(self):
        req = ExecutionRequest(
            request_id="r2", context_id="e2", timestamp=2000.0,
            task_type="analyze", priority=1,
            payload={"data": "test"}, tags=["urgent"],
            metadata={"source": "user"},
        )
        assert req.request_id == "r2"
        assert req.task_type == "analyze"
        assert req.priority == 1
        assert req.payload == {"data": "test"}
        assert req.tags == ["urgent"]
        assert req.metadata == {"source": "user"}

    def test_immutable(self):
        req = ExecutionRequest("r3", "e3", 3000.0)
        with pytest.raises(FrozenInstanceError):
            req.request_id = "changed"

    def test_task_types(self):
        for t in ["process", "analyze", "generate", "transform"]:
            req = ExecutionRequest("r", "e", 1.0, task_type=t)
            assert req.task_type == t

    def test_priorities(self):
        for p in [1, 3, 5, 7, 10]:
            req = ExecutionRequest("r", "e", 1.0, priority=p)
            assert req.priority == p


# ============================================================
# 3. ExecutionCandidate Tests
# ============================================================

class TestExecutionCandidate:
    def test_create_minimal(self):
        c = ExecutionCandidate("c1", "e1", "r1", 1000.0)
        assert c.candidate_id == "c1"
        assert c.context_id == "e1"
        assert c.request_id == "r1"
        assert c.timestamp == 1000.0
        assert c.candidate_type == "task"
        assert c.estimated_effort == 0.0
        assert c.dependencies == []
        assert c.tags == []

    def test_create_full(self):
        c = ExecutionCandidate(
            candidate_id="c2", context_id="e2", request_id="r2",
            timestamp=2000.0, name="Test", description="Desc",
            candidate_type="batch", estimated_effort=3.5,
            dependencies=["c0"], tags=["test"], metadata={"key": "val"},
        )
        assert c.name == "Test"
        assert c.description == "Desc"
        assert c.candidate_type == "batch"
        assert c.estimated_effort == 3.5
        assert c.dependencies == ["c0"]
        assert c.tags == ["test"]
        assert c.metadata == {"key": "val"}

    def test_immutable(self):
        c = ExecutionCandidate("c3", "e3", "r3", 3000.0)
        with pytest.raises(FrozenInstanceError):
            c.candidate_id = "changed"

    def test_candidate_types(self):
        for t in ["task", "subprocess", "batch"]:
            c = ExecutionCandidate("c", "e", "r", 1.0, candidate_type=t)
            assert c.candidate_type == t


# ============================================================
# 4. ExecutionRegistry Tests
# ============================================================

class TestExecutionRegistry:
    def test_empty_on_create(self):
        reg = ExecutionRegistry()
        assert reg.is_empty
        assert reg.total_items == 0
        snap = reg.snapshot()
        assert snap.context_count == 0
        assert snap.request_count == 0
        assert snap.candidate_count == 0

    def test_register_and_get_context(self):
        reg = ExecutionRegistry()
        ctx = ExecutionContext("e1", 1000.0)
        reg.register_context(ctx)
        assert reg.get_context("e1") == ctx
        assert reg.get_context("nonexistent") is None
        assert not reg.is_empty

    def test_register_and_get_request(self):
        reg = ExecutionRegistry()
        req = ExecutionRequest("r1", "e1", 1000.0)
        reg.register_request(req)
        assert reg.get_request("r1") == req
        assert reg.get_request("nonexistent") is None

    def test_register_and_get_candidate(self):
        reg = ExecutionRegistry()
        c = ExecutionCandidate("c1", "e1", "r1", 1000.0)
        reg.register_candidate(c)
        assert reg.get_candidate("c1") == c
        assert reg.get_candidate("nonexistent") is None

    def test_list_contexts(self):
        reg = ExecutionRegistry()
        assert reg.list_contexts() == []
        reg.register_context(ExecutionContext("e1", 1.0))
        reg.register_context(ExecutionContext("e2", 2.0))
        assert len(reg.list_contexts()) == 2

    def test_list_requests(self):
        reg = ExecutionRegistry()
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        reg.register_request(ExecutionRequest("r2", "e2", 2.0))
        assert len(reg.list_requests()) == 2

    def test_list_candidates(self):
        reg = ExecutionRegistry()
        reg.register_candidate(ExecutionCandidate("c1", "e1", "r1", 1.0))
        reg.register_candidate(ExecutionCandidate("c2", "e2", "r2", 2.0))
        assert len(reg.list_candidates()) == 2

    def test_clear_contexts(self):
        reg = ExecutionRegistry()
        reg.register_context(ExecutionContext("e1", 1.0))
        reg.clear_contexts()
        assert reg.get_context("e1") is None
        assert reg.list_contexts() == []

    def test_clear_requests(self):
        reg = ExecutionRegistry()
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        reg.clear_requests()
        assert reg.list_requests() == []

    def test_clear_candidates(self):
        reg = ExecutionRegistry()
        reg.register_candidate(ExecutionCandidate("c1", "e1", "r1", 1.0))
        reg.clear_candidates()
        assert reg.list_candidates() == []

    def test_clear_all(self):
        reg = ExecutionRegistry()
        reg.register_context(ExecutionContext("e1", 1.0))
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        reg.register_candidate(ExecutionCandidate("c1", "e1", "r1", 1.0))
        reg.clear_all()
        assert reg.is_empty
        assert reg.total_items == 0

    def test_snapshot(self):
        reg = ExecutionRegistry()
        reg.register_context(ExecutionContext("e1", 1.0))
        reg.register_context(ExecutionContext("e2", 2.0))
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        snap = reg.snapshot()
        assert snap.context_count == 2
        assert snap.request_count == 1
        assert snap.candidate_count == 0
        assert "e1" in snap.context_ids
        assert "r1" in snap.request_ids

    def test_total_items(self):
        reg = ExecutionRegistry()
        assert reg.total_items == 0
        reg.register_context(ExecutionContext("e1", 1.0))
        assert reg.total_items == 1
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        assert reg.total_items == 2
        reg.register_candidate(ExecutionCandidate("c1", "e1", "r1", 1.0))
        assert reg.total_items == 3

    def test_snapshot_frozen(self):
        reg = ExecutionRegistry()
        snap = reg.snapshot()
        with pytest.raises(FrozenInstanceError):
            snap.context_ids = ("x",)


# ============================================================
# 5. ExecutionBuilder Tests
# ============================================================

class TestExecutionBuilder:
    def test_build_immediate(self):
        b = ExecutionBuilder()
        c = b.build_immediate("c1", "e1", "r1", 1000.0, name="imm1")
        assert c.candidate_id == "c1"
        assert c.candidate_type == "immediate"
        assert "immediate" in c.tags
        assert c.metadata.get("type") == "immediate"
        assert c.name == "imm1"

    def test_build_scheduled(self):
        b = ExecutionBuilder()
        c = b.build_scheduled("c2", "e2", "r2", 2000.0, schedule_time=5000.0)
        assert c.candidate_type == "scheduled"
        assert c.metadata.get("schedule_time") == 5000.0
        assert "scheduled" in c.tags

    def test_build_conditional(self):
        b = ExecutionBuilder()
        c = b.build_conditional("c3", "e3", "r3", 3000.0, condition="if_ready")
        assert c.candidate_type == "conditional"
        assert c.metadata.get("condition") == "if_ready"
        assert "conditional" in c.tags

    def test_build_batch(self):
        b = ExecutionBuilder()
        c = b.build_batch("c4", "e4", "r4", 4000.0, batch_size=10)
        assert c.candidate_type == "batch"
        assert c.metadata.get("batch_size") == 10
        assert "batch" in c.tags

    def test_build_pipeline(self):
        b = ExecutionBuilder()
        c = b.build_pipeline("c5", "e5", "r5", 5000.0, steps=3)
        assert c.candidate_type == "pipeline"
        assert c.metadata.get("steps") == 3
        assert "pipeline" in c.tags

    def test_build_all_types_unique(self):
        b = ExecutionBuilder()
        candidates = [
            b.build_immediate("c1", "e1", "r1", 1.0),
            b.build_scheduled("c2", "e1", "r1", 1.0),
            b.build_conditional("c3", "e1", "r1", 1.0),
            b.build_batch("c4", "e1", "r1", 1.0),
            b.build_pipeline("c5", "e1", "r1", 1.0),
        ]
        types = {c.candidate_type for c in candidates}
        assert types == {"immediate", "scheduled", "conditional", "batch", "pipeline"}
        assert len(candidates) == 5

    def test_builder_default_names(self):
        b = ExecutionBuilder()
        c = b.build_immediate("c1", "e1", "r1", 1.0)
        assert c.name == "immediate_c1"
        c = b.build_scheduled("c2", "e1", "r1", 1.0)
        assert c.name == "scheduled_c2"

    def test_builder_effort(self):
        b = ExecutionBuilder()
        c = b.build_immediate("c1", "e1", "r1", 1.0, estimated_effort=2.5)
        assert c.estimated_effort == 2.5


# ============================================================
# 6. ConversationExecution Bridge Tests
# ============================================================

class TestConversationExecution:
    def test_queries_on_empty(self):
        reg = ExecutionRegistry()
        conv = ConversationExecution(reg)
        assert conv.get_execution_context("x") is None
        assert conv.get_execution_request("x") is None
        assert conv.get_execution_candidate("x") is None
        assert conv.list_all_contexts() == []
        assert conv.list_all_requests() == []
        assert conv.list_all_candidates() == []
        assert conv.count_contexts() == 0
        assert conv.count_requests() == 0
        assert conv.count_candidates() == 0
        snap = conv.get_registry_snapshot()
        assert snap.context_count == 0

    def test_queries_with_data(self):
        reg = ExecutionRegistry()
        ctx = ExecutionContext("e1", 1000.0)
        req = ExecutionRequest("r1", "e1", 1000.0)
        c = ExecutionCandidate("c1", "e1", "r1", 1000.0)
        reg.register_context(ctx)
        reg.register_request(req)
        reg.register_candidate(c)
        conv = ConversationExecution(reg)
        assert conv.get_execution_context("e1") == ctx
        assert conv.get_execution_request("r1") == req
        assert conv.get_execution_candidate("c1") == c
        assert len(conv.list_all_contexts()) == 1
        assert len(conv.list_all_requests()) == 1
        assert len(conv.list_all_candidates()) == 1
        assert conv.count_contexts() == 1
        assert conv.count_requests() == 1
        assert conv.count_candidates() == 1


# ============================================================
# 7. DashboardExecution Bridge Tests
# ============================================================

class TestDashboardExecution:
    def test_cards_on_empty(self):
        reg = ExecutionRegistry()
        dash = DashboardExecution(reg)
        oc = dash.overview_card()
        assert oc.status == "ready"
        assert oc.metrics["total_items"] == 0
        cc = dash.context_card()
        assert cc.status == "empty"
        rc = dash.request_card()
        assert rc.status == "empty"
        candc = dash.candidate_card()
        assert candc.status == "empty"
        sc = dash.summary_card()
        assert sc.status == "ready"
        stc = dash.status_card()
        assert stc.status == "idle"

    def test_cards_with_data(self):
        reg = ExecutionRegistry()
        reg.register_context(ExecutionContext("e1", 1.0))
        reg.register_request(ExecutionRequest("r1", "e1", 1.0))
        reg.register_candidate(ExecutionCandidate("c1", "e1", "r1", 1.0))
        dash = DashboardExecution(reg)
        oc = dash.overview_card()
        assert oc.metrics["total_items"] == 3
        cc = dash.context_card()
        assert cc.status == "active"
        assert "e1" in cc.items
        stc = dash.status_card()
        assert stc.status == "populated"

    def test_all_cards_frozen(self):
        reg = ExecutionRegistry()
        dash = DashboardExecution(reg)
        for card in [dash.overview_card(), dash.context_card(),
                     dash.request_card(), dash.candidate_card(),
                     dash.summary_card(), dash.status_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"
            assert isinstance(card, ExecutionCard)


# ============================================================
# 8. ExecutionRuntime Tests
# ============================================================

class TestExecutionRuntime:
    def test_create(self):
        rt = ExecutionRuntime()
        assert rt.registry.is_empty
        assert rt.builder is not None
        assert rt.conversation is not None
        assert rt.dashboard is not None

    def test_run(self):
        rt = ExecutionRuntime()
        ctx = ExecutionContext("e1", 1000.0)
        req = ExecutionRequest("r1", "e1", 1000.0)
        draft = rt.run(ctx, req)
        assert isinstance(draft, ExecutionDraft)
        assert draft.context_id == "e1"
        assert draft.candidates >= 1
        assert "immediate" in draft.types_used
        assert not rt.registry.is_empty

    def test_run_registers_data(self):
        rt = ExecutionRuntime()
        rt.run(ExecutionContext("e2", 2000.0), ExecutionRequest("r2", "e2", 2000.0))
        assert rt.registry.get_context("e2") is not None
        assert rt.registry.get_request("r2") is not None

    def test_conversation_after_run(self):
        rt = ExecutionRuntime()
        rt.run(ExecutionContext("e3", 3000.0), ExecutionRequest("r3", "e3", 3000.0))
        assert rt.conversation.count_contexts() == 1
        assert rt.conversation.count_requests() == 1

    def test_dashboard_after_run(self):
        rt = ExecutionRuntime()
        rt.run(ExecutionContext("e4", 4000.0), ExecutionRequest("r4", "e4", 4000.0))
        oc = rt.dashboard.overview_card()
        assert oc.metrics["total_items"] >= 2


# ============================================================
# 9. Immutability Tests
# ============================================================

def test_all_dtos_frozen():
    """Verifikasi semua DTO immutable."""
    for obj in [
        ExecutionContext("e", 1.0),
        ExecutionRequest("r", "e", 1.0),
        ExecutionCandidate("c", "e", "r", 1.0),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 10. Forbidden Imports Scan
# ============================================================

class TestForbiddenImports:
    def test_0_forbidden_imports(self):
        """AST scan: tidak ada forbidden imports di file source."""
        import ast, os, pathlib

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
# 11. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_context_parametrized(i):
    ctx = ExecutionContext(f"e{i}", float(i * 100))
    assert ctx.context_id == f"e{i}"
    assert ctx.timestamp == float(i * 100)


@pytest.mark.parametrize("i", list(range(1, 31)))
def test_request_parametrized(i):
    req = ExecutionRequest(f"r{i}", f"e{i}", float(i * 50),
                          task_type=["process", "analyze", "generate", "transform"][i % 4],
                          priority=(i % 10) + 1)
    assert req.request_id == f"r{i}"
    assert 1 <= req.priority <= 10


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_candidate_parametrized(i):
    c = ExecutionCandidate(f"c{i}", f"e{i}", f"r{i}", float(i * 100))
    assert c.candidate_id == f"c{i}"
    assert c.context_id == f"e{i}"


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_builder_parametrized(i):
    b = ExecutionBuilder()
    c = b.build_immediate(f"c{i}", f"e{i}", f"r{i}", float(i * 100))
    assert c.candidate_type == "immediate"
    assert not c.dependencies


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_registry_parametrized(i):
    reg = ExecutionRegistry()
    for j in range(i):
        reg.register_context(ExecutionContext(f"e{j}", float(j)))
    assert reg.snapshot().context_count == i


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    reg = ExecutionRegistry()
    for j in range(i):
        reg.register_request(ExecutionRequest(f"r{j}", f"e{j}", float(j)))
    conv = ConversationExecution(reg)
    assert conv.count_requests() == i


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_dashboard_parametrized(i):
    reg = ExecutionRegistry()
    for j in range(i):
        reg.register_context(ExecutionContext(f"e{j}", float(j)))
        reg.register_candidate(ExecutionCandidate(f"c{j}", f"e{j}", f"r{j}", float(j)))
    dash = DashboardExecution(reg)
    oc = dash.overview_card()
    assert oc.metrics["total_contexts"] == i
    assert oc.metrics["total_candidates"] == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_runtime_parametrized(i):
    rt = ExecutionRuntime()
    ctx = ExecutionContext(f"e{i}", float(i * 100))
    req = ExecutionRequest(f"r{i}", f"e{i}", float(i * 100))
    draft = rt.run(ctx, req)
    assert draft.context_id == f"e{i}"
    assert draft.candidates >= 1
