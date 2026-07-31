"""Sprint 269 - Monitoring.

Program D - Runtime Services & Deployment.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.metrics import RuntimeMetrics
from sam.runtime_service.service_monitor import ServiceMonitor
from sam.runtime_service.statistics import RuntimeStatistics, compute_statistics
from sam.runtime_service.runtime_snapshot import RuntimeSnapshot
from sam.runtime_service.report import RuntimeReport


def test_metrics_immutable():
    m = RuntimeMetrics(name="svc", counters={"events": 5})
    assert m.get("events") == 5
    assert m.get("missing", 9) == 9
    with pytest.raises(Exception):
        m.name = "x"


def test_metrics_as_dict():
    m = RuntimeMetrics(name="svc", counters={"a": 1})
    ad = m.as_dict()
    assert ad["counters"]["a"] == 1
    assert ad["name"] == "svc"


def test_monitor_record():
    mon = ServiceMonitor()
    mon.record("svc", "events")
    assert mon.get_metrics("svc").get("events") == 1


def test_monitor_record_increment():
    mon = ServiceMonitor()
    mon.record("svc", "events", 3)
    mon.record("svc", "events", 2)
    assert mon.get_metrics("svc").get("events") == 5


def test_monitor_services():
    mon = ServiceMonitor()
    mon.record("b", "e")
    mon.record("a", "e")
    assert mon.services() == ["a", "b"]


def test_monitor_log_events():
    mon = ServiceMonitor()
    mon.log("info", "started")
    mon.log("error", "boom")
    ev = mon.events()
    assert ev[0]["level"] == "info"
    assert ev[1]["message"] == "boom"


def test_stats_compute():
    m1 = RuntimeMetrics(name="a", counters={"events": 2})
    m2 = RuntimeMetrics(name="b", counters={"events": 5})
    st = compute_statistics({"a": m1, "b": m2})
    assert st.total_events == 7
    assert st.service_counts["a"] == 2


def test_stats_empty():
    st = compute_statistics({})
    assert st.total_events == 0
    assert st.service_counts == {}


def test_stats_immutable():
    st = RuntimeStatistics(service_counts={"a": 1}, total_events=1)
    with pytest.raises(Exception):
        st.total_events = 99


def test_snapshot_immutable():
    s = RuntimeSnapshot(services={"svc": "running"})
    assert s.healthy is True
    assert s.version == "27.0.0"
    with pytest.raises(Exception):
        s.healthy = False


def test_snapshot_as_dict():
    s = RuntimeSnapshot(services={"a": "ready"}, healthy=True,
                        extra={"x": 1})
    ad = s.as_dict()
    assert ad["services"] == {"a": "ready"}
    assert ad["extra"] == {"x": 1}


def test_report_immutable():
    r = RuntimeReport(title="t", services=["a"])
    with pytest.raises(Exception):
        r.title = "x"


def test_report_add_returns_new():
    r = RuntimeReport(title="t", services=["a"])
    r2 = r.add(status="ok")
    assert r2.sections["status"] == "ok"
    assert r.sections == {}  # yang lama tidak berubah


def test_report_as_dict():
    r = RuntimeReport(title="t", sections={"s": 1})
    assert r.as_dict()["title"] == "t"
    assert r.as_dict()["sections"] == {"s": 1}


def test_monitor_integration_snapshot():
    mon = ServiceMonitor()
    mon.record("connector", "events", 4)
    mon.record("provider", "events", 6)
    metrics = {s: mon.get_metrics(s) for s in mon.services()}
    st = compute_statistics(metrics)
    assert st.total_events == 10


def test_monitor_get_missing_metrics():
    mon = ServiceMonitor()
    assert mon.get_metrics("nope") is None
