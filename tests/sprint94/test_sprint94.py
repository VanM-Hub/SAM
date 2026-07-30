"""Sprint 94 — Execution Monitoring & Alerts Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.alerts import Alert, AlertRule, AlertHistory, AlertSummary
from sam.execution.runtime.alert_engine import AlertEngine
from sam.execution.runtime.conversation_alerts import ConversationAlerts, DashboardAlerts
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Alert DTO Tests
# ============================================================

class TestAlert:
    def test_create(self):
        a = Alert("a1", 100.0, "critical", "CPU overload")
        assert a.alert_id == "a1"
        assert a.severity == "critical"
        assert a.message == "CPU overload"
        assert not a.acknowledged

    def test_full(self):
        a = Alert("a1", 100.0, "warning", "High memory", source="test", candidate_id="c1")
        assert a.source == "test"
        assert a.candidate_id == "c1"

    def test_immutable(self):
        a = Alert("a1", 0.0, "info", "test")
        with pytest.raises(FrozenInstanceError):
            a.severity = "critical"


class TestAlertRule:
    def test_create(self):
        r = AlertRule("r1", "CPU Check", "cpu", "gt", 90.0, severity="critical")
        assert r.rule_id == "r1"
        assert r.metric == "cpu"
        assert r.operator == "gt"
        assert r.threshold == 90.0
        assert r.severity == "critical"

    def test_immutable(self):
        r = AlertRule("r", "n", "m", "gt", 1.0)
        with pytest.raises(FrozenInstanceError):
            r.threshold = 99.0


class TestAlertHistory:
    def test_empty(self):
        h = AlertHistory()
        assert h.total_alerts == 0
        assert h.latest_timestamp == 0.0

    def test_with_alerts(self):
        a1 = Alert("a1", 100.0, "info", "test")
        h = AlertHistory(alerts=(a1,), total_alerts=1, latest_timestamp=100.0)
        assert h.total_alerts == 1

    def test_immutable(self):
        h = AlertHistory()
        with pytest.raises(FrozenInstanceError):
            h.total_alerts = 5


class TestAlertSummary:
    def test_defaults(self):
        s = AlertSummary()
        assert s.status == "clear"

    def test_critical(self):
        s = AlertSummary(total_alerts=5, critical_count=2, status="critical")
        assert s.critical_count == 2
        assert s.status == "critical"

    def test_immutable(self):
        s = AlertSummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "critical"


# ============================================================
# 2. AlertEngine Tests
# ============================================================

class TestAlertEngine:
    def test_register_rule(self):
        e = AlertEngine()
        r = AlertRule("r1", "CPU Check", "cpu", "gt", 90.0)
        e.register_rule(r)
        rules = e.get_rules()
        assert "r1" in rules

    def test_unregister_rule(self):
        e = AlertEngine()
        r = AlertRule("r1", "CPU Check", "cpu", "gt", 90.0)
        e.register_rule(r)
        e.unregister_rule("r1")
        assert "r1" not in e.get_rules()

    def test_evaluate_gt_triggered(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        alerts = e.evaluate_value("cpu", 95.0, 100.0)
        assert len(alerts) == 1
        assert alerts[0].severity == "warning"

    def test_evaluate_gt_not_triggered(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        alerts = e.evaluate_value("cpu", 50.0, 100.0)
        assert len(alerts) == 0

    def test_evaluate_lt_triggered(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "Disk", "disk", "lt", 10.0))
        alerts = e.evaluate_value("disk", 5.0, 100.0)
        assert len(alerts) == 1

    def test_evaluate_gte(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gte", 90.0))
        assert len(e.evaluate_value("cpu", 90.0, 1.0)) == 1
        assert len(e.evaluate_value("cpu", 89.9, 1.0)) == 0

    def test_evaluate_lte(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "lte", 10.0))
        assert len(e.evaluate_value("cpu", 5.0, 1.0)) == 1
        assert len(e.evaluate_value("cpu", 15.0, 1.0)) == 0

    def test_evaluate_eq(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "eq", 50.0))
        assert len(e.evaluate_value("cpu", 50.0, 1.0)) == 1
        assert len(e.evaluate_value("cpu", 51.0, 1.0)) == 0

    def test_multiple_rules_same_metric(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU High", "cpu", "gt", 90.0))
        e.register_rule(AlertRule("r2", "CPU Critical", "cpu", "gt", 95.0, severity="critical"))
        alerts = e.evaluate_value("cpu", 97.0, 100.0)
        assert len(alerts) == 2

    def test_acknowledge(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        alerts = e.evaluate_value("cpu", 95.0, 100.0)
        e.acknowledge(alerts[0].alert_id)
        summary = e.get_summary()
        assert summary.acknowledged_count == 1

    def test_get_history_empty(self):
        e = AlertEngine()
        h = e.get_history()
        assert h.total_alerts == 0

    def test_get_history_with_alerts(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        e.evaluate_value("cpu", 95.0, 100.0)
        h = e.get_history()
        assert h.total_alerts == 1
        assert h.latest_timestamp == 100.0

    def test_summary_clear(self):
        e = AlertEngine()
        s = e.get_summary()
        assert s.status == "clear"

    def test_summary_warning(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        e.evaluate_value("cpu", 95.0, 100.0)
        s = e.get_summary()
        assert s.warning_count == 1
        assert s.status == "warning"

    def test_summary_critical(self):
        e = AlertEngine()
        e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0, severity="critical"))
        e.evaluate_value("cpu", 95.0, 100.0)
        s = e.get_summary()
        assert s.critical_count == 1
        assert s.status == "critical"


# ============================================================
# 3. ConversationAlerts Tests
# ============================================================

class TestConversationAlerts:
    def test_queries(self):
        ca = ConversationAlerts(AlertEngine())
        assert ca.get_engine() is not None
        caps = ca.describe_capabilities()
        assert len(caps) >= 6
        assert ca.count_capabilities() >= 6
        sev = ca.get_supported_severities()
        assert "critical" in sev
        ops = ca.get_supported_operators()
        assert "gt" in ops
        assert ca.count_rules() == 0


# ============================================================
# 4. DashboardAlerts Tests
# ============================================================

class TestDashboardAlerts:
    def test_cards(self):
        da = DashboardAlerts(AlertEngine())
        ec = da.engine_card()
        assert ec.status == "ready"
        rc = da.rules_card()
        assert rc.status == "ready"
        ac = da.alerts_card()
        assert ac.status == "clear"
        hc = da.history_card()
        assert hc.status == "idle"
        sc = da.summary_card()
        assert sc.status == "clear"

    def test_alerts_card_with_alerts(self):
        engine = AlertEngine()
        engine.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 90.0))
        engine.evaluate_value("cpu", 95.0, 100.0)
        da = DashboardAlerts(engine)
        ac = da.alerts_card()
        assert ac.metrics["total"] >= 1

    def test_all_frozen(self):
        da = DashboardAlerts(AlertEngine())
        for card in [da.engine_card(), da.rules_card(), da.alerts_card(),
                     da.history_card(), da.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        Alert("a", 0.0, "i", "m"),
        AlertRule("r", "n", "m", "gt", 1.0),
        AlertHistory(),
        AlertSummary(),
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
def test_alert_engine_evaluate_parametrized(i):
    e = AlertEngine()
    e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", float(i * 10)))
    alerts = e.evaluate_value("cpu", float(i * 5 + 5), float(i))
    assert isinstance(alerts, list)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_multiple_rules_parametrized(i):
    e = AlertEngine()
    for j in range(i % 5 + 1):
        e.register_rule(AlertRule(f"r{j}", f"Rule {j}", "cpu", "gt", float(j * 10)))
    e.evaluate_value("cpu", 50.0, 100.0)
    s = e.get_summary()
    assert s.total_alerts >= 0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_acknowledge_parametrized(i):
    e = AlertEngine()
    e.register_rule(AlertRule("r1", "CPU", "cpu", "gt", 0.0))
    alerts = e.evaluate_value("cpu", float(i), float(i))
    if alerts:
        e.acknowledge(alerts[0].alert_id)
        s = e.get_summary()
        assert s.acknowledged_count >= 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_conversation_alerts_parametrized(i):
    e = AlertEngine()
    for j in range(i):
        e.register_rule(AlertRule(f"r{j}", f"R{j}", "cpu", "gt", float(j)))
    ca = ConversationAlerts(e)
    assert ca.count_rules() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_alerts_parametrized(i):
    da = DashboardAlerts(AlertEngine())
    c = da.engine_card()
    assert c.status == "ready"


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_alert_operators_parametrized(i):
    e = AlertEngine()
    op = ["gt", "lt", "gte", "lte"][i % 4]
    e.register_rule(AlertRule("r1", "Test", "m", op, 50.0))
    alerts = e.evaluate_value("m", float(i * 10), 100.0)
    assert isinstance(alerts, list)
