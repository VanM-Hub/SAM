"""Sprint 240 — Generic Model Interface.

Program B — Model Runtime Integration.
DTO: ModelRequest, ModelResponse, Message, Context, Parameters. Tidak mengenal provider.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.model_message import ModelMessage
from sam.model_runtime.model_context import ModelContext
from sam.model_runtime.model_parameters import ModelParameters
from sam.model_runtime.model_request import ModelRequest
from sam.model_runtime.model_response import ModelResponse
from sam.model_runtime.model_validator import ModelValidator, ModelValidationResult
from sam.model_runtime.conversation_model_interface import (
    ConversationModelInterface,
    ConversationTurn,
)
from sam.model_runtime.dashboard_model_interface import DashboardModelInterface


def test_message_roles_immutable():
    m = ModelMessage(role="user", content="hi")
    assert m.content == "hi"
    with pytest.raises(ValueError):
        ModelMessage(role="evil", content="x")
    with pytest.raises(Exception):
        m.content = "changed"
    for role in ("system", "user", "assistant", "tool"):
        assert ModelMessage(role=role, content="x").role == role


def test_context_immutable_with_message():
    ctx = ModelContext(system="be nice")
    ctx2 = ctx.with_message(ModelMessage(role="user", content="hello"))
    assert len(ctx.messages) == 0
    assert len(ctx2.messages) == 1
    assert ctx2.messages[0].role == "user"


def test_parameters_immutable_merged():
    p = ModelParameters(temperature=0.7, max_tokens=100)
    p2 = p.merged(temperature=0.2)
    assert p.temperature == 0.7
    assert p2.temperature == 0.2
    assert p2.max_tokens == 100
    assert isinstance(p.stop, tuple) is False or p.stop == ()


def test_request_immutable_no_provider():
    r = ModelRequest(
        request_id="r1",
        task="chat",
        context=ModelContext(messages=[ModelMessage(role="user", content="x")]),
    )
    assert r.external_calls == 0
    assert r.mode == "preview"
    d = r.as_dict()
    assert d["external_calls"] == 0
    with pytest.raises(Exception):
        r.task = "embedding"


def test_response_immutable():
    resp = ModelResponse(response_id="resp1", request_id="r1", content="ok")
    assert resp.ok is True
    assert resp.external_calls == 0
    assert resp.as_dict()["ok"] is True


def test_validator_valid_request():
    v = ModelValidator()
    r = ModelRequest(request_id="r1", task="chat", model_type="chat")
    res = v.validate_request(r)
    assert isinstance(res, ModelValidationResult)
    assert res.valid is True
    assert res.errors == []


def test_validator_invalid_request():
    v = ModelValidator()
    r = ModelRequest(request_id="", task="nonsense", model_type="ghost")
    res = v.validate_request(r)
    assert res.valid is False
    assert len(res.errors) >= 3


def test_validator_response():
    v = ModelValidator()
    good = ModelResponse(response_id="a", request_id="b")
    assert v.validate_response(good).valid is True
    bad = ModelResponse(response_id="", request_id="")
    assert v.validate_response(bad).valid is False


def test_conversation_interface_readonly():
    ci = ConversationModelInterface()
    r = ModelRequest(request_id="r1", task="chat")
    res = ci.validate(r)
    assert res.valid is True
    resp = ModelResponse(response_id="rr", request_id="r1", content="hello")
    turn = ConversationTurn(turn_id="t1", request=r, response=resp)
    ci.record(turn)
    assert ci.count() == 1
    assert ci.turns()[0].external_calls == 0
    assert ci.turns()[0].as_dict()["external_calls"] == 0


def test_dashboard_interface_rows_and_summary():
    di = DashboardModelInterface()
    r = ModelRequest(request_id="r1", task="chat")
    resp = ModelResponse(response_id="a", request_id="r1", content="ok")
    di.add(r, resp)
    bad = ModelResponse(response_id="b", request_id="r1", ok=False,
                        error_code="ERR", error_message="x")
    di.add(r, bad)
    assert len(di.rows()) == 2
    s = di.summary()
    assert s["total"] == 2
    assert s["ok"] == 1
    assert s["failed"] == 1
    assert s["external_calls"] == 0


def test_no_provider_coupling():
    """Interface harus tidak mengenal provider — tidak import sam.providers/llm."""
    import sam.model_runtime.model_request as mr
    import inspect
    src = inspect.getsource(mr)
    assert "providers" not in src
    assert "llm" not in src.lower().replace("llm_adapter", "")


def test_forbidden_imports_absent():
    import inspect
    import sam.model_runtime.model_validator as mv
    src = inspect.getsource(mv)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
