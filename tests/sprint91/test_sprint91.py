"""Sprint 91 — Execution Resources Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.resource_plan import (
    ResourcePlan, ResourceAllocation, ResourceLimits,
    ResourceAvailability, ResourceSummary,
)
from sam.execution.runtime.resource_allocator import ResourceAllocator
from sam.execution.runtime.conversation_resources import ConversationResources
from sam.execution.runtime.dashboard_resources import DashboardResources
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Resource DTO Tests
# ============================================================

class TestResourcePlan:
    def test_create_minimal(self):
        p = ResourcePlan("rp1", "ep1")
        assert p.plan_id == "rp1"
        assert p.execution_plan_id == "ep1"
        assert p.total_cpu_units == 0.0
        assert p.resource_type == "standard"
        assert p.notes == ""

    def test_create_full(self):
        p = ResourcePlan("rp2", "ep2", total_cpu_units=10.5, total_memory_mb=512.0,
                        resource_type="high_perf", notes="test")
        assert p.total_cpu_units == 10.5
        assert p.total_memory_mb == 512.0
        assert p.resource_type == "high_perf"
        assert p.notes == "test"

    def test_immutable(self):
        p = ResourcePlan("rp", "ep")
        with pytest.raises(FrozenInstanceError):
            p.plan_id = "changed"


class TestResourceAllocation:
    def test_create(self):
        a = ResourceAllocation("c1", cpu_units=2.0, memory_mb=128.0)
        assert a.candidate_id == "c1"
        assert a.cpu_units == 2.0
        assert a.memory_mb == 128.0

    def test_immutable(self):
        a = ResourceAllocation("c1")
        with pytest.raises(FrozenInstanceError):
            a.candidate_id = "changed"


class TestResourceLimits:
    def test_defaults(self):
        l = ResourceLimits()
        assert l.max_cpu_units == 100.0
        assert l.max_memory_mb == 4096.0
        assert l.max_storage_mb == 10240.0
        assert l.max_network_units == 1000.0
        assert l.max_duration_seconds == 3600.0
        assert l.max_concurrent_tasks == 10

    def test_immutable(self):
        l = ResourceLimits()
        with pytest.raises(FrozenInstanceError):
            l.max_cpu_units = 999


class TestResourceAvailability:
    def test_defaults(self):
        a = ResourceAvailability()
        assert a.available_cpu_units == 100.0
        assert a.available_memory_mb == 4096.0

    def test_immutable(self):
        a = ResourceAvailability()
        with pytest.raises(FrozenInstanceError):
            a.available_cpu_units = 999


class TestResourceSummary:
    def test_defaults(self):
        s = ResourceSummary()
        assert s.total_plans == 0
        assert s.utilization_percent == 0.0
        assert s.status == "idle"

    def test_immutable(self):
        s = ResourceSummary()
        with pytest.raises(FrozenInstanceError):
            s.total_plans = 5


# ============================================================
# 2. ResourceAllocator Tests
# ============================================================

class TestResourceAllocator:
    def test_allocate_single(self):
        alloc = ResourceAllocator()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)
        a = alloc.allocate(c)
        assert a.candidate_id == "c1"
        assert a.cpu_units > 0
        assert a.memory_mb > 0
        assert a.duration_seconds > 0

    def test_allocate_batch(self):
        alloc = ResourceAllocator()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0,
                              candidate_type="batch", metadata={"batch_size": 10})
        a = alloc.allocate(c)
        assert a.cpu_units > 1.0  # batch multiplier

    def test_allocate_pipeline(self):
        alloc = ResourceAllocator()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0,
                              candidate_type="pipeline", metadata={"steps": 4})
        a = alloc.allocate(c)
        assert a.cpu_units > 1.0

    def test_allocate_all(self):
        alloc = ResourceAllocator()
        candidates = [
            ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 5))
            for i in range(5)
        ]
        allocations = alloc.allocate_all(candidates)
        assert len(allocations) == 5
        assert all(isinstance(a, ResourceAllocation) for a in allocations)

    def test_build_plan(self):
        alloc = ResourceAllocator()
        candidates = [
            ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0),
            ExecutionCandidate("c2", "e1", "r1", 2.0, estimated_effort=20.0),
        ]
        plan = alloc.build_plan("rp1", "ep1", candidates)
        assert plan.total_cpu_units > 0
        assert plan.estimated_duration_seconds > 0
        assert isinstance(plan, ResourcePlan)

    def test_check_availability_ok(self):
        alloc = ResourceAllocator()
        allocations = [ResourceAllocation("c1", cpu_units=5.0, memory_mb=256.0)]
        avail = ResourceAvailability(available_cpu_units=50.0, available_memory_mb=1024.0)
        issues = alloc.check_availability(allocations, avail)
        assert issues == []

    def test_check_availability_exceeded(self):
        alloc = ResourceAllocator()
        allocations = [ResourceAllocation("c1", cpu_units=100.0, memory_mb=5000.0)]
        avail = ResourceAvailability(available_cpu_units=50.0, available_memory_mb=1024.0)
        issues = alloc.check_availability(allocations, avail)
        assert len(issues) >= 1

    def test_get_summary_empty(self):
        alloc = ResourceAllocator()
        summary = alloc.get_summary([], ResourceLimits())
        assert summary.total_plans == 0
        assert summary.status == "idle"

    def test_get_summary_with_plans(self):
        alloc = ResourceAllocator()
        plans = [
            ResourcePlan("rp1", "ep1", total_cpu_units=10.0),
            ResourcePlan("rp2", "ep2", total_cpu_units=20.0),
        ]
        summary = alloc.get_summary(plans, ResourceLimits(max_cpu_units=100.0))
        assert summary.total_plans == 2
        assert summary.total_cpu_allocated == 30.0
        assert summary.utilization_percent == 30.0
        assert summary.status == "active"


# ============================================================
# 3. ConversationResources Tests
# ============================================================

class TestConversationResources:
    def test_queries(self):
        alloc = ResourceAllocator()
        cr = ConversationResources(alloc)
        assert cr.get_allocator() is alloc
        limits = cr.describe_default_limits()
        assert limits["max_cpu"] == 100.0
        assert limits["max_concurrent"] == 10
        avail = cr.default_availability()
        assert avail.available_cpu_units == 100.0
        assert cr.count_resource_types() == 4
        assert cr.count_limits() == 6
        assert len(cr.get_resource_types()) == 4

    def test_allocation_summary_empty(self):
        cr = ConversationResources(ResourceAllocator())
        summary = cr.allocation_summary([])
        assert summary["total_cpu"] == 0.0

    def test_allocation_summary_with_data(self):
        cr = ConversationResources(ResourceAllocator())
        allocations = [ResourceAllocation("c1", cpu_units=5.0, memory_mb=256.0)]
        summary = cr.allocation_summary(allocations)
        assert summary["total_cpu"] == 5.0
        assert summary["total_memory"] == 256.0


# ============================================================
# 4. DashboardResources Tests
# ============================================================

class TestDashboardResources:
    def test_cards(self):
        dr = DashboardResources(ResourceAllocator())
        pc = dr.plan_card()
        assert pc.status == "ready"
        lc = dr.limits_card()
        assert lc.metrics["max_cpu"] == 100.0
        ac = dr.availability_card()
        assert ac.status == "available"
        alc = dr.allocation_card()
        assert alc.metrics["allocator_ready"]
        sc = dr.summary_card()
        assert sc.status == "idle"

    def test_all_frozen(self):
        dr = DashboardResources(ResourceAllocator())
        for card in [dr.plan_card(), dr.limits_card(), dr.availability_card(),
                     dr.allocation_card(), dr.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        ResourcePlan("p", "ep"), ResourceAllocation("c"),
        ResourceLimits(), ResourceAvailability(), ResourceSummary(),
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
def test_allocator_parametrized(i):
    alloc = ResourceAllocator()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 3))
    a = alloc.allocate(c)
    assert a.cpu_units > 0


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_allocator_batch_parametrized(i):
    alloc = ResourceAllocator()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                          candidate_type="batch",
                          metadata={"batch_size": i * 2},
                          estimated_effort=float(i))
    a = alloc.allocate(c)
    assert a.cpu_units > 0


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_allocator_pipeline_parametrized(i):
    alloc = ResourceAllocator()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                          candidate_type="pipeline",
                          metadata={"steps": i},
                          estimated_effort=float(i))
    a = alloc.allocate(c)
    assert a.duration_seconds > 0


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_build_plan_parametrized(i):
    alloc = ResourceAllocator()
    candidates = [
        ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j))
        for j in range(i)
    ]
    plan = alloc.build_plan(f"rp{i}", "ep1", candidates)
    assert plan.total_cpu_units >= 0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_conversation_resources_parametrized(i):
    cr = ConversationResources(ResourceAllocator())
    assert cr.count_resource_types() == 4
    assert cr.count_limits() == 6


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_check_availability_parametrized(i):
    alloc = ResourceAllocator()
    allocations = [
        ResourceAllocation(f"c{j}", cpu_units=float(i * 5), memory_mb=float(i * 50))
        for j in range(i)
    ]
    avail = ResourceAvailability(available_cpu_units=100.0, available_memory_mb=4096.0)
    issues = alloc.check_availability(allocations, avail)
    assert isinstance(issues, list)
