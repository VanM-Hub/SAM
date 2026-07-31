"""Sprint 255 - Rollback Runtime.

Program C - Real Execution Runtime.
Rollback hanya metadata, tidak rollback external world.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.rollback_request import RollbackRequest
from sam.execution_runtime.rollback_plan import RollbackPlan
from sam.execution_runtime.rollback_report import RollbackReport
from sam.execution_runtime.rollback_summary import RollbackSummary
from sam.execution_runtime.rollback_runtime import RollbackRuntime, RollbackOutcome


def test_rollback_request_scope_metadata():
    r = RollbackRequest(rollback_id="rb1", execution_id="e1")
    assert r.scope == "metadata"
    assert r.mode == "rollback"
    assert r.as_dict()["scope"] == "metadata"


def test_rollback_request_immutable():
    r = RollbackRequest(rollback_id="rb1", execution_id="e1")
    with pytest.raises(Exception):
        r.execution_id = "e2"


def test_rollback_plan():
    r = RollbackRequest(rollback_id="rb1", execution_id="e1")
    p = RollbackPlan(plan_id="p1", request=r, metadata_keys=("a", "b"))
    assert p.scope == "metadata"
    assert p.external_calls == 0
    assert p.as_dict()["metadata_keys"] == ["a", "b"]


def test_rollback_report():
    r = RollbackReport(report_id="r1", rollback_id="rb1", execution_id="e1",
                       restored_metadata=("a",))
    assert r.status == "ok"
    assert r.external_calls == 0
    assert r.as_dict()["restored_metadata"] == ["a"]


def test_rollback_report_failed():
    r = RollbackReport(report_id="r2", rollback_id="rb2", execution_id="e2",
                       status="failed", error="boom")
    assert r.as_dict()["error"] == "boom"
    assert r.status == "failed"


def test_rollback_summary_counts():
    s = RollbackSummary()
    s = s.add(RollbackReport("r1", "rb1", "e1"))
    s = s.add(RollbackReport("r2", "rb2", "e2", status="failed"))
    assert s.total == 2
    assert s.ok == 1
    assert s.failed == 1
    assert s.external_calls == 0
    assert s.to_dict()["total"] == 2


def test_rollback_runtime_capture_and_restore():
    rt = RollbackRuntime()
    req = RollbackRequest(rollback_id="rb1", execution_id="e1")
    out = rt.run(req)
    # tanpa snapshot, tetap berhasil "restore" 0 key
    assert isinstance(out, RollbackOutcome)
    assert out.report.status == "ok"
    assert out.external_calls == 0
    assert out.report.restored_metadata == ()


def test_rollback_runtime_with_snapshot():
    rt = RollbackRuntime()
    rt.capture_metadata("mission-x", {"state": "done"})
    out = rt.run(RollbackRequest(rollback_id="rb2", execution_id="e2"))
    assert "mission-x" in out.report.restored_metadata
    assert out.report.status == "ok"
    assert out.external_calls == 0


def test_rollback_no_external_world_call():
    # Rollback tidak pernah memicu network / subprocess
    rt = RollbackRuntime()
    rt.capture_metadata("k", "v")
    out = rt.run(RollbackRequest(rollback_id="rb3", execution_id="e3"))
    assert out.external_calls == 0
    assert out.plan.scope == "metadata"


def test_rollback_summary_immutable():
    s0 = RollbackSummary()
    s1 = s0.add(RollbackReport("r1", "rb1", "e1"))
    assert s0.total == 0
    assert s1.total == 1


def test_rollback_runtime_summary_aggregates():
    rt = RollbackRuntime()
    rt.run(RollbackRequest(rollback_id="rb1", execution_id="e1"))
    rt.run(RollbackRequest(rollback_id="rb2", execution_id="e2"))
    s = rt.summary()
    assert s["total"] == 2
    assert s["ok"] == 2


def test_rollback_outcome_as_dict():
    rt = RollbackRuntime()
    out = rt.run(RollbackRequest(rollback_id="rb1", execution_id="e1"))
    d = out.as_dict()
    assert d["external_calls"] == 0
    assert d["report"]["status"] == "ok"


def test_no_forbidden_imports_rollback():
    import inspect
    import sam.execution_runtime.rollback_runtime as rr
    src = inspect.getsource(rr)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
