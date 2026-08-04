"""Session 02 - Conversation Preview Wiring (Conversation -> ExecutionRuntime preview).

ConversationPreviewGateway mengirim action 'execution.preview' via RuntimeAPI
(reuse Session 01) -> ExecutionRuntime preview. Context dibawa di payload
namespace 'conversation' (AD-S02-001). Provider TIDAK dieksekusi (ADR-024).
"""
from __future__ import annotations

import pytest

from sam.runtime_service.api import (
    RuntimeAPI,
    ConversationExecutionContext,
    ConversationPreviewGateway,
    PreviewRequestView,
    wire_conversation_preview,
)
from sam.execution_runtime.execution_engine import ExecutionEngine
from sam.execution_runtime.execution_request import ExecutionRequest


def _make_build(engine):
    def _build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id,
            provider_id=view.provider_id,
            operation=view.operation,
            mode="preview",
            payload={
                "conversation": {
                    "conversation_id": "session-01",
                    "request": "status",
                    "turn_id": "t1",
                }
            },
        )
    return _build


def _make_exec(engine):
    return lambda req: engine.execute(req)


@pytest.fixture
def cgw():
    api = RuntimeAPI()
    engine = ExecutionEngine()
    wire_conversation_preview(
        api,
        build_request=_make_build(engine),
        execute=_make_exec(engine),
    )
    g = ConversationPreviewGateway(api)
    return api, g


def test_conversation_preview_gateway_executes_preview(cgw):
    api, g = cgw
    ctx = ConversationExecutionContext(
        conversation_id="session-01", request="status", turn_id="t1")
    res = g.preview(ctx, execution_id="exec-c-1")
    assert res.executed is False      # tidak ada eksekusi nyata (ADR-024)
    assert res.external_calls == 0    # no network / no provider call
    assert res.mode == "preview"
    assert res.status == "preview"


def test_conversation_preview_never_executes(cgw):
    _, g = cgw
    ctx = ConversationExecutionContext(
        conversation_id="session-01", request="run", turn_id="t2")
    res = g.preview(ctx, execution_id="exec-c-2")
    # mode selalu preview; executed selalu False walau request "run"
    assert res.executed is False
    assert res.mode == "preview"


def test_conversation_preview_payload_namespace(cgw):
    api, g = cgw
    # verifikasi handler tetap menerima payload namespace conversation
    from sam.runtime_service.api import APIRequest
    resp = api.handle(APIRequest(
        action="execution.preview", request_id="r1",
        payload={"execution_id": "e1", "provider_id": "filesystem",
                 "operation": "conversation.preview",
                 "payload": {"conversation": {"conversation_id": "s1", "request": "x"}}}),
    )
    assert resp.is_ok()
    assert resp.data["executed"] is False
    assert resp.data["mode"] == "preview"


def test_conversation_preview_result_immutable():
    from sam.runtime_service.api import ConversationPreviewResult
    r = ConversationPreviewResult(executed=False, approved=True)
    with pytest.raises(Exception):
        r.executed = True


def test_conversation_preview_result_dict():
    from sam.runtime_service.api import ConversationPreviewResult
    r = ConversationPreviewResult(executed=False, approved=False, external_calls=0,
                                   mode="preview", status="preview")
    d = r.as_dict()
    assert d["executed"] is False
    assert d["mode"] == "preview"
