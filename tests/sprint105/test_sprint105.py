"""Sprint 105 — Runtime Health Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_health import (
    HealthCheck, HealthReport, ResourceUsage, HealthThreshold, AlertRecord,
)
from sam.runtime_kernel.health_checker import HealthChecker
from sam.runtime_kernel.health_engine import HealthEngine
from sam.runtime_kernel.resource_monitor import ResourceMonitor
from sam.runtime_kernel.health_aggregator import HealthAggregator
from sam.runtime_kernel.conversation_health import ConversationHealth, DashboardHealth
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestHealthCheck:
    def test_create(self):
        h = HealthCheck("h1", "guardian", "healthy", 5.0)
        assert h.status == "healthy"

    def test_immutable(self):
        h = HealthCheck("h", "g")
        with pytest.raises(FrozenInstanceError):
            h.status = "unhealthy"


class TestHealthReport:
    def test_create(self):
        r = HealthReport("r1", 100.0, "healthy", [])
        assert r.overall == "healthy"

    def test_immutable(self):
        r = HealthReport("r", 0.0)
        with pytest.raises(FrozenInstanceError):
            r.overall = "unhealthy"


class TestResourceUsage:
    def test_create(self):
        u = ResourceUsage("u1", 45.0, 60.0, "kernel")
        assert u.cpu_pct == 45.0

    def test_immutable(self):
        u = ResourceUsage("u")
        with pytest.raises(FrozenInstanceError):
            u.cpu_pct = 50.0


class TestHealthThreshold:
    def test_create(self):
        t = HealthThreshold("t1", "cpu", 75.0, 90.0)
        assert t.warning == 75.0

    def test_immutable(self):
        t = HealthThreshold("t", "cpu")
        with pytest.raises(FrozenInstanceError):
            t.warning = 80.0


class TestAlertRecord:
    def test_create(self):
        a = AlertRecord("a1", "cpu", 95.0, "critical")
        assert a.level == "critical"

    def test_immutable(self):
        a = AlertRecord("a", "cpu", 0.0)
        with pytest.raises(FrozenInstanceError):
            a.level = "warning"


# ============================================================
# 2. Engine Tests
# ============================================================

class TestHealthChecker:
    def test_check(self):
        c = HealthChecker()
        h = c.check("h1", "guardian", "healthy", 2.0)
        assert h.subsystem == "guardian"
        assert c.count_checks() == 1

    def test_get(self):
        c = HealthChecker()
        c.check("h1", "guardian")
        assert c.get("h1") is not None
        assert c.get("bogus") is None

    def test_generate_report(self):
        c = HealthChecker()
        c.check("h1", "guardian", "healthy")
        c.check("h2", "decision", "healthy")
        r = c.generate_report("r1", 100.0)
        assert r.overall == "healthy"
        assert len(r.checks) == 2

    def test_report_unhealthy(self):
        c = HealthChecker()
        c.check("h1", "guardian", "unhealthy")
        r = c.generate_report("r1", 100.0)
        assert r.overall == "unhealthy"

    def test_report_degraded(self):
        c = HealthChecker()
        c.check("h1", "guardian", "healthy")
        c.check("h2", "decision", "degraded")
        r = c.generate_report("r1", 100.0)
        assert r.overall == "degraded"

    def test_list_unhealthy(self):
        c = HealthChecker()
        c.check("h1", "guardian", "healthy")
        c.check("h2", "decision", "unhealthy")
        c.check("h3", "kernel", "degraded")
        assert len(c.list_unhealthy()) == 2


class TestHealthEngine:
    def test_add_threshold(self):
        e = HealthEngine()
        e.add_threshold(HealthThreshold("cpu", "cpu"))
        assert e.get_threshold("cpu") is not None

    def test_evaluate_info(self):
        e = HealthEngine()
        e.add_threshold(HealthThreshold("cpu", "cpu", 80.0, 95.0))
        a = e.evaluate_metric("a1", "cpu", 50.0)
        assert a.level == "info"
        assert e.count_alerts() == 1

    def test_evaluate_warning(self):
        e = HealthEngine()
        e.add_threshold(HealthThreshold("cpu", "cpu", 80.0, 95.0))
        a = e.evaluate_metric("a1", "cpu", 85.0)
        assert a.level == "warning"

    def test_evaluate_critical(self):
        e = HealthEngine()
        e.add_threshold(HealthThreshold("cpu", "cpu", 80.0, 95.0))
        a = e.evaluate_metric("a1", "cpu", 99.0)
        assert a.level == "critical"

    def test_evaluate_no_threshold(self):
        e = HealthEngine()
        a = e.evaluate_metric("a1", "bogus", 99.0)
        assert a.level == "info"

    def test_get_alerts(self):
        e = HealthEngine()
        e.evaluate_metric("a1", "cpu", 50.0)
        e.evaluate_metric("a2", "mem", 90.0)
        assert len(e.get_alerts()) == 2

    def test_overall_health(self):
        e = HealthEngine()
        r = HealthReport("r1", 0.0, "healthy")
        assert e.overall_health(r) == "healthy"


class TestResourceMonitor:
    def test_record(self):
        m = ResourceMonitor()
        u = m.record("u1", 45.0, 60.0)
        assert m.count() == 1
        assert u.cpu_pct == 45.0

    def test_get(self):
        m = ResourceMonitor()
        m.record("u1", 45.0, 60.0)
        assert m.get("u1") is not None

    def test_cpu_avg(self):
        m = ResourceMonitor()
        m.record("u1", 40.0, 50.0)
        m.record("u2", 60.0, 70.0)
        assert m.cpu_avg() == 50.0

    def test_cpu_avg_empty(self):
        m = ResourceMonitor()
        assert m.cpu_avg() == 0.0

    def test_memory_avg(self):
        m = ResourceMonitor()
        m.record("u1", 40.0, 50.0)
        m.record("u2", 60.0, 70.0)
        assert m.memory_avg() == 60.0


class TestHealthAggregator:
    def test_aggregate_healthy(self):
        a = HealthAggregator()
        r1 = HealthReport("r1", 0.0, "healthy")
        r2 = HealthReport("r2", 0.0, "healthy")
        assert a.aggregate([r1, r2]) == "healthy"

    def test_aggregate_unhealthy(self):
        a = HealthAggregator()
        r1 = HealthReport("r1", 0.0, "healthy")
        r2 = HealthReport("r2", 0.0, "unhealthy")
        assert a.aggregate([r1, r2]) == "unhealthy"

    def test_aggregate_degraded(self):
        a = HealthAggregator()
        r1 = HealthReport("r1", 0.0, "healthy")
        r2 = HealthReport("r2", 0.0, "degraded")
        assert a.aggregate([r1, r2]) == "degraded"

    def test_aggregate_empty(self):
        a = HealthAggregator()
        assert a.aggregate([]) == "unknown"

    def test_count_reports(self):
        a = HealthAggregator()
        r1 = HealthReport("r1", 0.0, "healthy")
        r2 = HealthReport("r2", 0.0, "healthy")
        assert a.count_reports([r1, r2]) == 2

    def test_merge_checks(self):
        a = HealthAggregator()
        c1 = HealthCheck("c1", "g", "healthy")
        c2 = HealthCheck("c2", "d", "healthy")
        r1 = HealthReport("r1", 0.0, "healthy", [c1])
        r2 = HealthReport("r2", 0.0, "healthy", [c2])
        merged = a.merge_checks([r1, r2])
        assert len(merged) == 2


# ============================================================
# 3. Conversation Health
# ============================================================

class TestConversationHealth:
    def test_queries(self):
        ch = ConversationHealth(HealthChecker(), HealthEngine(),
                                ResourceMonitor(), HealthAggregator())
        assert ch.get_checker() is not None
        assert ch.get_engine() is not None
        assert ch.get_monitor() is not None
        assert ch.get_aggregator() is not None
        layers = ch.describe_layers()
        assert len(layers) == 4
        assert ch.count_layers() == 4
        assert ch.get_health_status() == "healthy"
        assert ch.get_unhealthy_count() == 0


# ============================================================
# 4. Dashboard Health
# ============================================================

class TestDashboardHealth:
    def test_cards(self):
        dh = DashboardHealth(HealthChecker(), HealthEngine(),
                             ResourceMonitor(), HealthAggregator())
        for card in [dh.engine_card(), dh.checker_card(), dh.resource_card(),
                     dh.alert_card(), dh.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        dh = DashboardHealth(HealthChecker(), HealthEngine(),
                             ResourceMonitor(), HealthAggregator())
        for card in [dh.engine_card(), dh.checker_card(), dh.resource_card(),
                     dh.alert_card(), dh.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        HealthCheck("h", "g"),
        HealthReport("r", 0.0),
        ResourceUsage("u"),
        HealthThreshold("t", "cpu"),
        AlertRecord("a", "cpu", 0.0),
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
def test_checker_parametrized(i):
    c = HealthChecker()
    statuses = ["healthy", "healthy", "degraded", "healthy"]
    c.check(f"h{i}", f"sub{i % 4}", statuses[i % 4], float(i * 2))
    assert c.count_checks() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_threshold_parametrized(i):
    e = HealthEngine()
    e.add_threshold(HealthThreshold(f"cpu{i}", "cpu", float(70 + i % 20), 95.0))
    a = e.evaluate_metric(f"a{i}", f"cpu{i}", float(50 + i * 2))
    assert a.level in ("info", "warning", "critical")


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_resource_parametrized(i):
    m = ResourceMonitor()
    m.record(f"u{i}", float(i * 3), float(i * 4), f"sub{i % 3}")
    assert m.count() == 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_aggregator_parametrized(i):
    a = HealthAggregator()
    reports = [
        HealthReport(f"r{j}", float(j), "healthy" if j % 2 == 0 else "degraded")
        for j in range(i % 5 + 1)
    ]
    result = a.aggregate(reports)
    assert result in ("healthy", "degraded", "unknown")


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    ch = ConversationHealth(HealthChecker(), HealthEngine(),
                            ResourceMonitor(), HealthAggregator())
    assert ch.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    dh = DashboardHealth(HealthChecker(), HealthEngine(),
                         ResourceMonitor(), HealthAggregator())
    c = dh.engine_card()
    assert c.status == "ready"
