"""Sprint 251 - Execution Request.

Program C - Real Execution Runtime.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_response import ExecutionResponse
from sam.execution_runtime.execution_context import ExecutionContext
from sam.execution_runtime.execution_option import ExecutionOption
from sam.execution_runtime.execution_validation import (
    ExecutionValidation, ExecutionValidationEngine,
)
from sam.execution_runtime.conversation_execution_request import (
    ConversationExecutionRequest, ConversationExecutionRequestView,
)
from sam.execution_runtime.dashboard_execution_request import DashboardExecutionRequest


def test_request_required_fields():
    with pytest.raises(ValueError):
        ExecutionRequest(execution_id="", provider_id="openai", operation="run")
    with pytest.raises(ValueError):
        ExecutionRequest(execution_id="e1", provider_id="", operation="run")


def test_request_mode_validation():
    with pytest.raises(ValueError):
        ExecutionRequest(execution_id="e1", provider_id="p", operation="x", mode="bad")
    ExecutionRequest(execution_id="e1", provider_id="p", operation="x", mode="execute")


def test_request_timeout_retries_validation():
    with pytest.raises(ValueError):
        ExecutionRequest(execution_id="e1", provider_id="p", operation="x", timeout_seconds=0)
    with pytest.raises(ValueError):
        ExecutionRequest(execution_id="e1", provider_id="p", operation="x", max_retries=-1)


def test_request_support_fields():
    r = ExecutionRequest(execution_id="e1", provider_id="openai", operation="chat",
                         mode="execute", timeout_seconds=120, max_retries=3,
                         cancellation_token="tok-1")
    assert r.timeout_seconds == 120
    assert r.max_retries == 3
    assert r.cancellation_token == "tok-1"
    assert r.execution_id == "e1"
    assert r.provider_id == "openai"


def test_request_defaults():
    r = ExecutionRequest(execution_id="e1", provider_id="p", operation="x")
    assert r.mode == "preview"
    assert r.timeout_seconds == 60
    assert r.deterministic is True
    assert r.synchronous is True
    assert r.approved is False
    assert r.cancellation_token is None


def test_request_immutable():
    r = ExecutionRequest(execution_id="e1", provider_id="p", operation="x")
    with pytest.raises(Exception):
        r.provider_id = "o"


def test_request_as_dict():
    r = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                         payload={"k": "v"})
    ad = r.as_dict()
    assert ad["payload"] == {"k": "v"}
    assert ad["execution_id"] == "e1"


def test_response_status_and_succeeded():
    ok = ExecutionResponse(execution_id="e1", provider_id="p", operation="x", status="completed")
    fail = ExecutionResponse(execution_id="e1", provider_id="p", operation="x", status="failed", error="boom")
    assert ok.succeeded is True
    assert fail.succeeded is False
    assert fail.error == "boom"


def test_response_fields():
    r = ExecutionResponse(execution_id="e1", provider_id="p", operation="x",
                          mode="execute", external_calls=5, retries_used=1, duration_ms=20)
    assert r.external_calls == 5
    assert r.retries_used == 1
    assert r.duration_ms == 20
    assert r.as_dict()["mode"] == "execute"


def test_response_status_enum_values():
    valid = {"pending", "executing", "completed", "failed", "cancelled", "timeout"}
    assert ExecutionResponse(execution_id="e", provider_id="p", operation="x").status in valid


def test_context():
    c = ExecutionContext(context_id="ctx1", execution_id="e1", provider_ids=("openai", "ollama"))
    assert c.provider_ids == ("openai", "ollama")
    assert c.mode == "preview"
    assert c.as_dict()["provider_ids"] == ["openai", "ollama"]


def test_option():
    o = ExecutionOption(option_id="o1", name="fast", provider_id="openai",
                        timeout_seconds=30, max_retries=1)
    assert o.timeout_seconds == 30
    assert o.cancellable is True
    assert o.as_dict()["rollback"] is True


def test_validation_valid():
    v = ExecutionValidationEngine().validate("v1", ExecutionRequest(execution_id="e1", provider_id="p", operation="run"))
    assert isinstance(v, ExecutionValidation)
    assert v.valid is True
    assert v.errors == ()


def test_validation_invalid_empty_provider():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="")
    v = ExecutionValidationEngine().validate("v1", req)
    assert v.valid is False
    assert "operation required" in v.errors


def test_validation_warning_no_approval():
    req = ExecutionRequest(execution_id="e1", provider_id="p", operation="x",
                           mode="execute", approved=False)
    v = ExecutionValidationEngine().validate("v1", req)
    assert v.valid is True
    assert any("approval" in w for w in v.warnings)


def test_conversation_request_bridge():
    req = ExecutionRequest(execution_id="e1", provider_id="openai", operation="chat")
    view = ConversationExecutionRequest().view("conv-1", req)
    assert isinstance(view, ConversationExecutionRequestView)
    assert view.execution_id == "e1"
    assert view.provider_id == "openai"
    assert view.external_calls == 0


def test_dashboard_request_summary():
    dash = DashboardExecutionRequest()
    dash.add(ExecutionRequest(execution_id="e1", provider_id="p", operation="x"))
    dash.add(ExecutionRequest(execution_id="e2", provider_id="p", operation="x",
                              mode="execute", approved=False))
    dash.add(ExecutionRequest(execution_id="e3", provider_id="p", operation="x",
                              mode="execute", approved=True))
    assert len(dash.rows()) == 3
    s = dash.summary()
    assert s["execute_pending"] == 1
    assert s["external_calls"] == 0


def test_no_forbidden_imports_request():
    import inspect
    import sam.execution_runtime.execution_request as er
    src = inspect.getsource(er)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
