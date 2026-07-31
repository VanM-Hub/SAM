"""Sprint 250 - Execution Foundation.

Program C - Real Execution Runtime.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_descriptor import ExecutionDescriptor
from sam.execution_runtime.execution_contract import ExecutionContract
from sam.execution_runtime.execution_capability import ExecutionCapability
from sam.execution_runtime.execution_metadata import ExecutionMetadata
from sam.execution_runtime.execution_registry import ExecutionRegistry
from sam.execution_runtime.conversation_execution_foundation import (
    ConversationExecutionFoundation, ConversationExecutionFoundationView,
)
from sam.execution_runtime.dashboard_execution_foundation import (
    DashboardExecutionFoundation,
)


def test_descriptor_immutable_and_modes():
    d = ExecutionDescriptor(id="e1", name="Run", operation="run", mode="execute")
    assert d.provider == "generic"
    assert d.requires_approval is True
    with pytest.raises(Exception):
        d.name = "x"
    with pytest.raises(ValueError):
        ExecutionDescriptor(id="e2", name="B", operation="x", mode="bad-mode")


def test_descriptor_provider_from_ids():
    d = ExecutionDescriptor(id="e3", name="C", operation="x", mode="preview", provider_ids=["openai"])
    assert d.provider == "openai"
    valid_modes = {"preview", "execute", "rollback"}
    assert d.mode in valid_modes


def test_descriptor_as_dict():
    d = ExecutionDescriptor(id="e4", name="D", operation="op", mode="rollback", tags=["t1"])
    ad = d.as_dict()
    assert ad["id"] == "e4"
    assert ad["mode"] == "rollback"
    assert ad["category"] == "execution"


def test_contract_defaults():
    c = ExecutionContract(contract_id="c1", owner_id="o1")
    assert c.requires_approval is True
    assert c.max_retries == 2
    assert c.timeout_seconds == 60
    assert c.external_calls == 0
    assert isinstance(c.allowed_modes, list)
    assert "execute" in c.allowed_modes


def test_capability_can():
    cap = ExecutionCapability(capability_id="cap1", owner_id="o1", operations=frozenset({"run", "stop"}))
    assert cap.can("run") is True
    assert cap.can("list") is False
    cap2 = ExecutionCapability(capability_id="cap2", owner_id="o1")
    assert cap2.can("anything") is True  # empty = all ops allowed


def test_capability_flags():
    cap = ExecutionCapability(capability_id="cap3", owner_id="o1")
    assert cap.supports_execute is True
    assert cap.supports_rollback is True
    assert cap.supports_cancellation is True


def test_metadata_defaults():
    m = ExecutionMetadata(owner_id="o1")
    assert m.preview_only is True
    assert m.approved is False
    assert m.executed is False
    assert m.external_calls == 0
    assert m.synchronous is True
    assert m.determinism_check is True


def test_metadata_execute():
    m = ExecutionMetadata(owner_id="o1", mode="execute", preview_only=False,
                          approved=True, executed=True, external_calls=3)
    assert m.executed is True
    assert m.external_calls == 3
    ad = m.as_dict()
    assert ad["approved"] is True
    assert ad["mode"] == "execute"


def test_registry_modes():
    reg = ExecutionRegistry()
    reg.register(ExecutionDescriptor(id="p", name="P", operation="x", mode="preview"))
    reg.register(ExecutionDescriptor(id="x", name="X", operation="x", mode="execute"))
    reg.register(ExecutionDescriptor(id="r", name="R", operation="x", mode="rollback"))
    assert reg.count() == 3
    assert [d.id for d in reg.by_mode("execute")] == ["x"]
    assert reg.get("p").mode == "preview"
    assert reg.get("nope") is None
    valid = {"preview", "execute", "rollback"}
    assert {d.mode for d in reg.all()}.issubset(valid)


def test_registry_disallows_bad_mode():
    reg = ExecutionRegistry()
    try:
        reg.register(ExecutionDescriptor(id="b", name="B", operation="x", mode="bad"))
    except ValueError:
        pass
    assert reg.count() == 0


def test_conversation_foundation_view():
    reg = ExecutionRegistry()
    reg.register(ExecutionDescriptor(id="x", name="X", operation="x", mode="execute"))
    reg.register(ExecutionDescriptor(id="r", name="R", operation="x", mode="rollback"))
    conv = ConversationExecutionFoundation(reg)
    v = conv.view("conv-1")
    assert isinstance(v, ConversationExecutionFoundationView)
    assert v.available == 2
    assert v.execute_available == 1
    assert v.rollback_available == 1
    assert v.external_calls == 0


def test_dashboard_foundation_summary():
    dash = DashboardExecutionFoundation()
    dash.add(ExecutionDescriptor(id="x", name="X", operation="x", mode="execute"))
    dash.add(ExecutionDescriptor(id="p", name="P", operation="x", mode="preview"))
    assert len(dash.rows()) == 3
    s = dash.summary()
    assert s["total"] == 2
    assert s["by_mode"]["execute"] == 1
    assert s["external_calls"] == 0


def test_dashboard_foundation_registers_too():
    dash = DashboardExecutionFoundation()
    dash.add(ExecutionDescriptor(id="x", name="X", operation="x", mode="execute"))
    assert dash._registry.get("x") is not None


def test_no_forbidden_imports_foundation():
    import inspect
    import sam.execution_runtime.execution_descriptor as ed
    src = inspect.getsource(ed)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src


def test_execution_modes_enum_values():
    # hanya memastikan tiga mode diekspos di registry
    reg = ExecutionRegistry()
    for mode in ("preview", "execute", "rollback"):
        reg.register(ExecutionDescriptor(id=f"m-{mode}", name=mode, operation="x", mode=mode))
    assert set(reg._by_mode.keys()) == {"preview", "execute", "rollback"}
