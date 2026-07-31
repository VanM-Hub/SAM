"""Sprint 254 - Execution Engine.

Program C - Real Execution Runtime.
Pipeline: Request -> Validation -> Approval -> Dispatch -> Provider ->
Response -> Report. Network hanya saat execute+approved.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_response import ExecutionResponse
from sam.execution_runtime.execution_pipeline import (
    ExecutionPipeline, ExecutionPipelineResult, _ProviderExecutor,
)
from sam.execution_runtime.execution_report import ExecutionReport, StageTrace
from sam.execution_runtime.execution_summary import ExecutionSummary
from sam.execution_runtime.execution_runtime import ExecutionRuntime, ExecutionOutcome
from sam.execution_runtime.execution_engine import ExecutionEngine


def make_ok_handler(calls=0):
    def handler(req: ExecutionRequest) -> ExecutionResponse:
        return ExecutionResponse(
            execution_id=req.execution_id, provider_id=req.provider_id,
            operation=req.operation, status="completed", mode=req.mode,
            external_calls=calls,
        )
    return handler


def test_execution_pipeline_preview_no_call():
    req = ExecutionRequest("e1", "openai", "chat", mode="preview")
    pl = ExecutionPipeline()
    res = pl.run("PX1", req)
    assert isinstance(res, ExecutionPipelineResult)
    assert res.executed is False
    assert res.external_calls == 0
    assert res.response.status == "preview"


def test_execution_pipeline_execute_no_approval_blocked():
    req = ExecutionRequest("e1", "openai", "chat", mode="execute", approved=False)
    pl = ExecutionPipeline()
    res = pl.run("PX2", req)
    assert res.executed is False
    assert res.external_calls == 0
    assert res.response.status == "blocked"


def test_execution_pipeline_execute_approved_calls_provider():
    req = ExecutionRequest("e1", "openai", "chat", mode="execute",
                           approved=True, approver="van")
    pl = ExecutionPipeline()
    pl.executor.bind(make_ok_handler(calls=3))
    res = pl.run("PX3", req)
    assert res.executed is True
    assert res.external_calls == 3
    assert res.response.status == "completed"


def test_execution_pipeline_execute_approved_without_bound_handler_fails():
    req = ExecutionRequest("e1", "openai", "chat", mode="execute",
                           approved=True, approver="van")
    pl = ExecutionPipeline()
    res = pl.run("PX4", req)
    assert res.executed is False
    assert res.response.status == "failed"
    assert "no provider executor bound" in res.response.error


def test_execution_pipeline_report_stages():
    req = ExecutionRequest("e1", "openai", "chat", mode="preview")
    res = ExecutionPipeline().run("PX5", req)
    names = [s.stage for s in res.report.stages]
    assert names == ["request", "validation", "approval", "dispatch", "provider", "response", "report"]
    assert res.report.all_ok() is True


def test_execution_pipeline_report_status_preview():
    req = ExecutionRequest("e1", "openai", "chat", mode="preview")
    res = ExecutionPipeline().run("PX6", req)
    assert res.report.status == "pending"


def test_execution_pipeline_report_status_completed():
    req = ExecutionRequest("e1", "openai", "chat", mode="execute", approved=True, approver="v")
    pl = ExecutionPipeline()
    pl.executor.bind(make_ok_handler(calls=2))
    res = pl.run("PX7", req)
    assert res.report.status == "completed"
    assert res.report.external_calls == 2


def test_provider_executor_no_handler():
    ex = _ProviderExecutor()
    resp = ex.call(ExecutionRequest("e1", "openai", "chat"))
    assert resp.status == "failed"


def test_provider_executor_bound():
    ex = _ProviderExecutor()
    ex.bind(make_ok_handler(calls=1))
    resp = ex.call(ExecutionRequest("e1", "openai", "chat", mode="execute", approved=True))
    assert resp.status == "completed"


def test_execution_report_stage_lookup():
    r = ExecutionReport(report_id="r1", execution_id="e1", stages=(
        StageTrace("validation", "ok"), StageTrace("provider", "ok", 1),
    ))
    assert r.stage("provider").external_calls == 1
    assert r.stage("approval") is None


def test_execution_report_all_ok():
    r = ExecutionReport(report_id="r1", execution_id="e1", stages=(
        StageTrace("a", "ok"), StageTrace("b", "failed"),
    ))
    assert r.all_ok() is False
    assert r.as_dict()["execution_id"] == "e1"


def test_execution_summary_counts():
    s = ExecutionSummary()
    ok = ExecutionReport(report_id="r1", execution_id="e1", status="completed", external_calls=2)
    fail = ExecutionReport(report_id="r2", execution_id="e2", status="failed", external_calls=0)
    s = s.add(ok)
    s = s.add(fail)
    assert s.total == 2
    assert s.completed == 1
    assert s.failed == 1
    assert s.external_calls == 2
    assert s.to_dict()["total"] == 2


def test_summary_immutable():
    s0 = ExecutionSummary()
    s1 = s0.add(ExecutionReport(report_id="r1", execution_id="e1", status="completed"))
    assert s0.total == 0
    assert s1.total == 1


def test_execution_runtime_preview():
    rt = ExecutionRuntime()
    req = ExecutionRequest("e1", "openai", "chat", mode="preview")
    out = rt.run("R1", req)
    assert isinstance(out, ExecutionOutcome)
    assert out.approved is True
    assert out.executed is False
    assert out.external_calls == 0


def test_execution_runtime_execute_approved():
    req = ExecutionRequest("e1", "openai", "chat", mode="execute", approved=True, approver="v")
    pl = ExecutionPipeline()
    pl.executor.bind(make_ok_handler(calls=4))
    out = ExecutionRuntime(pipeline=pl).run("R2", req)
    assert out.approved is True
    assert out.executed is True
    assert out.external_calls == 4


def test_execution_engine_summary_aggregates():
    eng = ExecutionEngine()
    eng.execute(ExecutionRequest("e1", "openai", "chat", mode="preview"))
    pl = eng.runtime.pipeline
    pl.executor.bind(make_ok_handler(calls=5))
    eng.execute(ExecutionRequest("e2", "openai", "chat", mode="execute",
                                 approved=True, approver="v"))
    s = eng.summary()
    assert s["total"] == 2


def test_execution_outcome_as_dict():
    req = ExecutionRequest("e1", "openai", "chat", mode="preview")
    out = ExecutionRuntime().run("R3", req)
    d = out.as_dict()
    assert d["external_calls"] == 0
    assert d["executed"] is False


def test_no_forbidden_imports_engine():
    import inspect
    import sam.execution_runtime.execution_pipeline as ep
    src = inspect.getsource(ep)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
