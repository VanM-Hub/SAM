"""Sprint 246 — Model Runtime.

Program B — Model Runtime Integration.
Pipeline: Descriptor -> Request -> Validation -> Preview -> Report.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.model_descriptor import ModelDescriptor
from sam.model_runtime.model_request import ModelRequest
from sam.model_runtime.model_context import ModelContext
from sam.model_runtime.model_message import ModelMessage
from sam.model_runtime.model_pipeline import ModelPipeline, ModelPipelineLog, ModelPipelineStage
from sam.model_runtime.model_report import ModelReport, ModelReportBuilder
from sam.model_runtime.model_runtime import ModelRuntime, ModelRuntimeResult
from sam.model_runtime.model_session import ModelSession, ModelSessionStore
from sam.model_runtime.model_monitor import ModelMonitor, ModelHealth
from sam.model_runtime.model_statistics import ModelStatistics, ModelStatisticsCollector
from sam.model_runtime.conversation_runtime import ConversationRuntime
from sam.model_runtime.dashboard_runtime import DashboardRuntime


def make_req():
    return ModelRequest(
        request_id="r1", task="chat",
        context=ModelContext(messages=[ModelMessage(role="user", content="hi")]),
    )


def test_pipeline_success_five_stages():
    pipe = ModelPipeline()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    report = pipe.run(desc, make_req())
    assert isinstance(report, ModelReport)
    assert report.ok is True
    assert report.stages_completed == 5
    assert report.external_calls == 0
    log = pipe.log()
    assert isinstance(log, ModelPipelineLog)
    names = [s["name"] for s in log.as_dict()["stages"]]
    assert names == ["descriptor", "request", "validation", "preview", "report"]


def test_pipeline_validation_failure():
    pipe = ModelPipeline()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    bad = ModelRequest(request_id="", task="nonsense")
    report = pipe.run(desc, bad)
    assert report.ok is False
    assert report.stages_completed == 3
    assert report.errors


def test_report_builder():
    b = ModelReportBuilder()
    good = b.success(make_req(), None)
    assert good.ok is True
    assert good.stages_completed == 5
    failed = b.failed("rX", ["err"])
    assert failed.ok is False
    assert failed.errors == ["err"]


def test_model_runtime_run():
    rt = ModelRuntime()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    result = rt.run(desc, make_req())
    assert isinstance(result, ModelRuntimeResult)
    assert result.external_calls == 0
    assert result.report.ok is True
    assert rt.runtime_id == "model-runtime"
    assert rt.registry().count() == 0  # registry terpisah


def test_model_session_store():
    s = ModelSessionStore()
    sess = s.create("s1")
    assert isinstance(sess, ModelSession)
    assert s.get("s1") == sess
    rep = ModelReport(report_id="rep", request_id="r1")
    assert s.add_report("s1", rep) is True
    assert len(s.reports("s1")) == 1
    assert s.count() == 1


def test_monitor_health_metrics():
    mon = ModelMonitor()
    assert mon.health().healthy is True
    mon.observe(ModelReport(report_id="a", request_id="r1", ok=True))
    mon.observe(ModelReport(report_id="b", request_id="r2", ok=False))
    assert mon.health().healthy is False
    m = {x.name: x.value for x in mon.metrics()}
    assert m["reports"] == 2
    assert m["ok"] == 1
    assert m["failed"] == 1


def test_statistics_collector():
    mon = ModelMonitor()
    mon.observe(ModelReport(report_id="a", request_id="r1", ok=True))
    stats = ModelStatisticsCollector().collect(mon)
    assert isinstance(stats, ModelStatistics)
    assert stats.total_reports == 1
    assert stats.external_calls == 0


def test_conversation_runtime_bridge():
    conv = ConversationRuntime()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    out = conv.run("conv-1", desc, make_req())
    assert out.external_calls == 0
    assert out.result.report.ok is True


def test_dashboard_runtime_rows():
    mon = ModelMonitor()
    mon.observe(ModelReport(report_id="a", request_id="r1", ok=True))
    dash = DashboardRuntime(monitor=mon)
    assert dash.health().healthy is True
    assert len(dash.rows()) == 3
    s = dash.summary()
    assert s["total"] == 1
    assert s["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.model_pipeline as mp
    src = inspect.getsource(mp)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
