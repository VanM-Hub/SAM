"""Session 02 - Conversation Execution Builder (AD-S02-001).

ConversationContext -> ExecutionRequest(mode='preview') dengan payload
namespace 'conversation'. AD-S02-001: hanya namespace conversation diisi;
DTO/ExecutionRuntime/RuntimeService tidak diubah; payload serializable.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import (
    ConversationExecutionContext,
    ConversationExecutionRequestBuilder,
)
from sam.execution_runtime.execution_request import ExecutionRequest


def test_context_immutable():
    ctx = ConversationExecutionContext(conversation_id="c1", request="apa", turn_id="t1")
    with pytest.raises(Exception):
        ctx.conversation_id = "x"

    d = ctx.as_dict()
    assert d["conversation_id"] == "c1"
    assert d["request"] == "apa"
    assert d["turn_id"] == "t1"


def test_context_without_turn():
    ctx = ConversationExecutionContext(conversation_id="c2", request="oke")
    d = ctx.as_dict()
    assert d["conversation_id"] == "c2"
    assert d["request"] == "oke"
    assert "turn_id" not in d


def test_builder_creates_preview_request():
    b = ConversationExecutionRequestBuilder()
    req = b.build(
        context=ConversationExecutionContext(conversation_id="c3", request="cek"),
        provider_id="filesystem",
        operation="conversation.preview",
        execution_id="exec-1",
    )
    assert isinstance(req, ExecutionRequest)
    assert req.mode == "preview"          # ADR-024 preview-only
    assert req.provider_id == "filesystem"
    assert req.operation == "conversation.preview"


def test_builder_payload_only_conversation_namespace():
    """AD-S02-001: HANYA namespace 'conversation' yang diisi."""
    b = ConversationExecutionRequestBuilder()
    req = b.build(
        context=ConversationExecutionContext(
            conversation_id="c4", request="Tampilkan status", turn_id="t9"),
        provider_id="filesystem",
        operation="conversation.preview",
        execution_id="exec-2",
    )
    assert list(req.payload.keys()) == ["conversation"]
    conv = req.payload["conversation"]
    assert conv["conversation_id"] == "c4"
    assert conv["request"] == "Tampilkan status"
    assert conv["turn_id"] == "t9"


def test_builder_requires_fields():
    b = ConversationExecutionRequestBuilder()
    with pytest.raises(ValueError):
        b.build(
            context=ConversationExecutionContext(conversation_id="", request="x"),
            provider_id="filesystem", operation="op", execution_id="e")
    with pytest.raises(ValueError):
        b.build(
            context=ConversationExecutionContext(conversation_id="c", request=""),
            provider_id="filesystem", operation="op", execution_id="e")


def test_payload_uses_request_not_intent():
    """AD-S02-001: pakai 'request', BUKAN 'intent' (hindari ambiguitas S07)."""
    b = ConversationExecutionRequestBuilder()
    req = b.build(
        context=ConversationExecutionContext(conversation_id="c5", request="Pengguna meminta X"),
        provider_id="filesystem", operation="conversation.preview", execution_id="e5")
    conv = req.payload["conversation"]
    assert "request" in conv
    assert "intent" not in conv


def test_payload_serializable_plain_types():
    """Payload hanya berisi tipe serializable (str), bukan objek runtime."""
    from sam.runtime_service.api import (
        ConversationExecutionContext as C,
        ConversationExecutionRequestBuilder as B,
    )
    req = B().build(
        context=C(conversation_id="c6", request="hello", turn_id="t6"),
        provider_id="filesystem", operation="op", execution_id="e6")
    # pastikan payload flatten jadi primitif
    import json
    payload_json = json.loads(json.dumps(req.payload))
    assert payload_json["conversation"]["conversation_id"] == "c6"


def test_builder_no_execution_runtime_import():
    """Modul builder tidak menyentuh ExecutionRuntime (hanya DTO)."""
    from sam.runtime_service.api import conversation_execution_builder as mod
    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    assert "execution_runtime.execution_runtime" not in joined
    assert "execution_pipeline" not in joined
