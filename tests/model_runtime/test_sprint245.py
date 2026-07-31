"""Sprint 245 — Tool Calling.

Program B — Model Runtime Integration.
Generic. Tidak execute tool.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.tool_descriptor import ToolDescriptor
from sam.model_runtime.tool_call import ToolCall
from sam.model_runtime.tool_arguments import ToolArguments
from sam.model_runtime.tool_result import ToolResult
from sam.model_runtime.tool_preview import ToolPreviewEngine, ToolPreview
from sam.model_runtime.tool_validator import ToolValidator
from sam.model_runtime.conversation_tool import ConversationTool
from sam.model_runtime.dashboard_tool import DashboardTool


def make_tool():
    return ToolDescriptor(
        tool_id="t1", name="search", description="look up",
        parameters_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        required=["q"],
    )


def test_tool_descriptor_immutable():
    t = make_tool()
    assert t.external_calls == 0
    assert t.preview_only is True
    with pytest.raises(Exception):
        t.name = "x"


def test_tool_call_not_executed():
    t = make_tool()
    call = ToolCall(call_id="c1", tool=t, arguments={"q": "hello"})
    assert call.external_calls == 0
    assert call.as_dict()["preview_only"] is True


def test_tool_arguments_complete():
    t = make_tool()
    args = ToolArguments(tool_id="t1", values={"q": "x"},
                         provided=["q"], missing=[])
    assert args.complete is True
    missing_args = ToolArguments(tool_id="t1", values={}, provided=[], missing=["q"])
    assert missing_args.complete is False


def test_tool_result_not_executed():
    r = ToolResult(call_id="c1", data={"ok": 1})
    assert r.executed is False
    assert r.external_calls == 0
    assert r.as_dict()["executed"] is False


def test_tool_preview_no_execution():
    t = make_tool()
    eng = ToolPreviewEngine()
    pv = eng.preview(t, {"q": "hello"})
    assert isinstance(pv, ToolPreview)
    assert pv.would_execute is False
    assert "not executed" in pv.note
    assert pv.external_calls == 0
    assert len(pv.calls) == 1
    assert pv.calls[0].external_calls == 0


def test_tool_arguments_builder():
    t = make_tool()
    eng = ToolPreviewEngine()
    args = eng.build_arguments(t, {"foo": 1})
    assert args.missing == ["q"]  # required "q" tidak diberikan
    full = eng.build_arguments(t, {"q": "x"})
    assert full.missing == []


def test_tool_validator():
    t = make_tool()
    v = ToolValidator()
    good = ToolArguments(tool_id="t1", values={"q": "x"}, provided=["q"], missing=[])
    assert v.validate_arguments(t, good).valid is True
    bad = ToolArguments(tool_id="t1", values={}, provided=[], missing=["q"])
    assert v.validate_arguments(t, bad).valid is False
    executed = ToolResult(call_id="c1", executed=True)
    assert v.validate_result(executed).valid is False


def test_conversation_tool_bridge():
    conv = ConversationTool()
    out = conv.call_preview("conv-1", make_tool(), {"q": "hi"})
    assert out.external_calls == 0
    assert out.preview.would_execute is False


def test_dashboard_tool_rows():
    t = make_tool()
    eng = ToolPreviewEngine()
    pv = eng.preview(t, {"q": "x"})
    dash = DashboardTool()
    dash.add(pv)
    assert len(dash.rows()) == 1
    assert dash.rows()[0].call_count == 1
    assert dash.summary()["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.tool_preview as tp
    src = inspect.getsource(tp)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
