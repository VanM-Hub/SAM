"""Sprint 256 - Monitoring.

Program C - Real Execution Runtime.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_metrics import ExecutionMetrics
from sam.execution_runtime.execution_health import ExecutionHealth
from sam.execution_runtime.execution_history import (
    ExecutionHistory, ExecutionHistoryEntry,
)
from sam.execution_runtime.execution_snapshot import ExecutionSnapshot
from sam.execution_runtime.execution_monitor import ExecutionMonitor
from sam.execution_runtime.execution_report import ExecutionReport
from sam.execution_runtime.conversation_execution_monitoring import (
    ConversationExecutionMonitoring, ConversationExecutionMonitoringView,
)
from sam.execution_runtime.dashboard_execution_monitoring import DashboardExecutionMonitoring


def test_metrics():
    m = ExecutionMetrics(metrics_id="m1", execution_id="e1", duration_ms=100,
                         retries=2, external_calls=5)
    assert m.duration_ms == 100
    assert m.retries == 2
    assert m.external_calls == 5
    assert m.as_dict()["execution_id"] == "e1"


def test_health_default_ok():
    h = ExecutionHealth(health_id="h1")
    assert h.ok is True
    assert h.status == "healthy"
    assert h.external_calls == 0


def test_health_degraded():
    h = ExecutionHealth(health_id="h2", ok=False, provider_available=False, status="down")
    assert h.ok is False
    assert h.provider_available is False
    assert h.status == "down"


def test_history_record_from_report():
    h = ExecutionHistory()
    r = ExecutionReport(report_id="r1", execution_id="e1", status="completed", external_calls=2)
    e = h.record(r)
    assert isinstance(e, ExecutionHistoryEntry)
    assert e.entry_id == "eh-1"
    assert e.status == "completed"
    assert e.external_calls == 2


def test_history_append_only_and_find():
    h = ExecutionHistory()
    h.record(ExecutionReport("r1", "e1", status="completed"))
    h.record(ExecutionReport("r2", "e2", status="failed"))
    assert h.count() == 2
    assert h.find("e2").status == "failed"
    assert h.find("nope") is None


def test_history_all_returns_copy():
    h = ExecutionHistory()
    h.record(ExecutionReport("r1", "e1", status="completed"))
    h.all().clear()
    assert h.count() == 1


def test_snapshot():
    snap = ExecutionSnapshot(snapshot_id="s1", health=ExecutionHealth(health_id="h1"),
                             total_recorded=3, external_calls_total=4)
    assert snap.total_recorded == 3
    assert snap.external_calls_total == 4
    assert snap.as_dict()["health"]["ok"] is True


def test_monitor_default_health():
    mon = ExecutionMonitor()
    assert mon.health().ok is True
    assert mon.history.count() == 0


def test_monitor_record_aggregates():
    mon = ExecutionMonitor()
    mon.record_report(ExecutionReport("r1", "e1", status="completed"))
    mon.record_report(ExecutionReport("r2", "e2", status="failed"))
    assert mon.history.count() == 2


def test_monitor_snapshot_metrics():
    mon = ExecutionMonitor()
    mon.add_metrics(ExecutionMetrics("m1", "e1", external_calls=2))
    mon.add_metrics(ExecutionMetrics("m2", "e2", external_calls=3))
    snap = mon.snapshot("s1")
    assert snap.total_recorded == 0  # belum ada history
    assert snap.external_calls_total == 5


def test_conversation_monitoring_bridge():
    mon = ExecutionMonitor()
    mon.record_report(ExecutionReport("r1", "e1", status="completed"))
    conv = ConversationExecutionMonitoring(mon)
    v = conv.view("conv-1")
    assert isinstance(v, ConversationExecutionMonitoringView)
    assert v.recorded == 1
    assert v.healthy is True
    assert v.external_calls == 0


def test_dashboard_monitoring_summary():
    mon = ExecutionMonitor()
    mon.record_report(ExecutionReport("r1", "e1", status="completed"))
    dash = DashboardExecutionMonitoring(mon)
    s = dash.summary()
    assert s["recorded"] == 1
    assert s["healthy"] is True
    assert s["external_calls"] == 0


def test_no_forbidden_imports_monitoring():
    import inspect
    import sam.execution_runtime.execution_monitor as em
    src = inspect.getsource(em)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
