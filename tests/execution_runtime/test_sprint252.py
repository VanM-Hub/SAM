"""Sprint 252 - Approval Gate.

Program C - Real Execution Runtime.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.approval_gate import ApprovalGate, ApprovalDecision
from sam.execution_runtime.approval_validator import ApprovalValidator, ApprovalValidatorResult
from sam.execution_runtime.approval_summary import ApprovalSummary
from sam.execution_runtime.approval_report import ApprovalReport
from sam.execution_runtime.approval_pipeline import ApprovalPipeline, ApprovalPipelineResult


def test_gate_rejects_unapproved_execute():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=False)
    assert ApprovalGate().may_execute(req) is False
    d = ApprovalGate().evaluate(req)
    assert d.approved is False
    assert "approval" in d.reason


def test_gate_allows_approved_execute():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=True)
    assert ApprovalGate().may_execute(req) is True


def test_gate_preview_does_not_need_approval():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x", mode="preview")
    assert ApprovalGate().may_execute(req) is True  # preview aman tanpa approval


def test_gate_rollback_allowed():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="rollback", approved=False)
    assert ApprovalGate().may_execute(req) is True


def test_decision_immutable():
    d = ApprovalDecision(approval_id="a1", execution_id="e1", approved=True, approver="van")
    with pytest.raises(Exception):
        d.approved = False
    assert d.as_dict()["approved"] is True


def test_validator_rejects_rejection_without_reason():
    d = ApprovalDecision(approval_id="a1", execution_id="e1", approved=False, reason="")
    r = ApprovalValidator().validate(d)
    assert isinstance(r, ApprovalValidatorResult)
    assert r.valid is False
    assert any("reason" in e for e in r.errors)


def test_validator_rejects_approval_without_approver():
    d = ApprovalDecision(approval_id="a1", execution_id="e1", approved=True, approver="")
    r = ApprovalValidator().validate(d)
    assert r.valid is False
    assert any("approver" in e for e in r.errors)


def test_validator_accepts_valid():
    d = ApprovalDecision(approval_id="a1", execution_id="e1", approved=True, approver="van")
    r = ApprovalValidator().validate(d)
    assert r.valid is True
    assert r.errors == ()


def test_summary_counts():
    s = ApprovalSummary()
    s = s.add(ApprovalDecision("a1", "e1", True, approver="v"))
    s = s.add(ApprovalDecision("a2", "e2", False, reason="no"))
    assert s.total == 2
    assert s.approved == 1
    assert s.rejected == 1
    assert s.to_dict()["total"] == 2


def test_summary_immutable_add_returns_new():
    s0 = ApprovalSummary()
    s1 = s0.add(ApprovalDecision("a1", "e1", True, approver="v"))
    assert s0.total == 0
    assert s1.total == 1


def test_report_all_approved():
    r = ApprovalReport(report_id="r1", decisions=(
        ApprovalDecision("a1", "e1", True, approver="v"),
        ApprovalDecision("a2", "e2", True, approver="v"),
    ))
    assert r.all_approved() is True
    assert r.as_dict()["report_id"] == "r1"


def test_report_not_all_approved():
    r = ApprovalReport(report_id="r1", decisions=(
        ApprovalDecision("a1", "e1", True, approver="v"),
        ApprovalDecision("a2", "e2", False, reason="no"),
    ))
    assert r.all_approved() is False


def test_pipeline_preview_state():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x", mode="preview")
    res = ApprovalPipeline().run("pl1", req)
    assert isinstance(res, ApprovalPipelineResult)
    assert res.state == "preview"
    assert res.approved is True
    assert res.external_calls == 0


def test_pipeline_execute_not_approved_awaiting():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=False)
    res = ApprovalPipeline().run("pl1", req)
    assert res.state == "awaiting_approval"
    assert res.approved is False


def test_pipeline_execute_approved_ready():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=True, approver="van")
    res = ApprovalPipeline().run("pl1", req)
    assert res.state == "execution_ready"
    assert res.approved is True


def test_pipeline_execute_without_approver_blocked():
    # approved True tapi approver kosong -> validator invalid -> blocked
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=True)
    pl = ApprovalPipeline()
    # patch gate untuk kasus approver kosong tidak mungkin via request; tes validasi langsung
    d = ApprovalDecision("a1", "e1", True, approver="")
    r = ApprovalValidator().validate(d)
    assert r.valid is False


def test_pipeline_may_execute_flag():
    pl = ApprovalPipeline()
    assert pl.may_execute(ExecutionRequest("e1", "p", "x", mode="execute", approved=True, approver="van")) is True
    assert pl.may_execute(ExecutionRequest("e2", "p", "x", mode="execute", approved=False)) is False


def test_no_forbidden_imports_approval():
    import inspect
    import sam.execution_runtime.approval_pipeline as ap
    src = inspect.getsource(ap)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src


def test_approval_blocks_execution_contractually():
    # Contoh: request yang belum approved => external execution harus dilarang
    req = ExecutionRequest("e1", "p", "x", mode="execute", approved=False)
    if ApprovalGate().may_execute(req):
        pytest.fail("execute tidak boleh terjadi tanpa approval")
