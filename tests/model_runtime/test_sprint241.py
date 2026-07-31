"""Sprint 241 — Chat Model.

Program B — Model Runtime Integration.
Support: system, user, assistant, tool. Preview only.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.chat_model import ChatModel
from sam.model_runtime.chat_builder import ChatBuilder
from sam.model_runtime.chat_history import ChatHistory, ChatHistoryEntry
from sam.model_runtime.chat_session import ChatSession, ChatSessionStore
from sam.model_runtime.chat_preview import ChatPreviewEngine, ChatPreview
from sam.model_runtime.chat_summary import ChatSummarizer, ChatSummary
from sam.model_runtime.conversation_chat import ConversationChat, ChatModelSource
from sam.model_runtime.dashboard_chat import DashboardChat
from sam.model_runtime.model_message import ModelMessage
from sam.model_runtime.model_request import ModelRequest
from sam.model_runtime.model_context import ModelContext


def test_chat_model_immutable():
    c = ChatModel(chat_id="c1", name="ChatGPT")
    assert c.preview_only is True
    assert c.external_calls == 0
    with pytest.raises(Exception):
        c.name = "X"
    assert c.as_dict()["external_calls"] == 0


def test_builder_supports_all_roles():
    b = ChatBuilder()
    model = b.build_model("c1", "ChatGPT")
    assert model.supports_system and model.supports_tool
    ctx = b.context(
        system="be nice",
        messages=[b.system("sys"), b.user("hi"), b.assistant("yo"), b.tool("r", "t1")],
    )
    roles = [m.role for m in ctx.messages]
    assert roles == ["system", "user", "assistant", "tool"]


def test_history_append_and_len():
    h = ChatHistory("h1")
    e = h.append(ModelMessage(role="user", content="hi"))
    assert isinstance(e, ChatHistoryEntry)
    assert len(h) == 1
    assert h.messages()[0].content == "hi"
    assert h.as_dict()["history_id"] == "h1"


def test_session_store():
    store = ChatSessionStore()
    c = ChatModel(chat_id="c1", name="M")
    s = store.create("s1", c)
    assert isinstance(s, ChatSession)
    assert store.get("s1") == s
    store.add_message("s1", ModelMessage(role="user", content="hello"))
    assert len(store.history("s1")) == 1
    assert store.count() == 1
    with pytest.raises(KeyError):
        store.history("missing")


def test_chat_preview_deterministic_no_network():
    engine = ChatPreviewEngine()
    ctx = ModelContext(
        system="sys",
        messages=[ModelMessage(role="user", content="halo dunia")],
    )
    req = ModelRequest(request_id="r1", task="chat", context=ctx)
    pv = engine.preview(req)
    assert isinstance(pv, ChatPreview)
    assert pv.external_calls == 0
    assert "user" in pv.detected_roles
    assert pv.estimated_tokens > 0
    assert "no inference" in pv.plan_note


def test_chat_summary():
    h = ChatHistory("s1")
    h.append(ModelMessage(role="user", content="a b c"))
    h.append(ModelMessage(role="assistant", content="d e"))
    summ = ChatSummarizer().summarize(h)
    assert isinstance(summ, ChatSummary)
    assert summ.total_messages == 2
    assert summ.role_counts == {"user": 1, "assistant": 1}


def test_conversation_chat_bridge():
    chat = ChatModel(chat_id="c1", name="M")
    conv = ConversationChat()
    res = conv.attach("conv-1", ChatModelSource(chat))
    assert res.external_calls == 0
    assert res.session.session_id == "conv-1"
    assert conv.send("conv-1", "ping") is True


def test_dashboard_chat_rows():
    store = ChatSessionStore()
    chat = ChatModel(chat_id="c1", name="M")
    store.create("s1", chat)
    store.add_message("s1", ModelMessage(role="user", content="hi"))
    dash = DashboardChat(store)
    rows = dash.rows()
    assert len(rows) == 1
    assert rows[0].total_messages == 1
    s = dash.summary()
    assert s["sessions"] == 1
    assert s["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.chat_preview as cp
    src = inspect.getsource(cp)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
