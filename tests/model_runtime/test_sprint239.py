"""Sprint 239 — Model Foundation.

Program B — Model Runtime Integration.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.model_descriptor import ModelDescriptor
from sam.model_runtime.model_capability import ModelCapability
from sam.model_runtime.model_contract import ModelContract
from sam.model_runtime.model_metadata import ModelMetadata
from sam.model_runtime.model_registry import ModelRegistry
from sam.model_runtime.model_builder import ModelBuilder, ModelFoundationBuilder
from sam.model_runtime.conversation_model_foundation import (
    ConversationModelFoundation,
    ConversationModelBinding,
)
from sam.model_runtime.dashboard_model_foundation import (
    DashboardModelFoundation,
    DashboardModelCard,
)


def test_descriptor_immutable_and_required():
    d = ModelDescriptor(id="m1", name="Chat-1", model_type="chat")
    assert d.model_type == "chat"
    assert d.preview_only if hasattr(d, "preview_only") else True
    with pytest.raises(Exception):
        d.name = "x"  # frozen
    with pytest.raises(ValueError):
        ModelDescriptor(id="", name="x")
    with pytest.raises(ValueError):
        ModelDescriptor(id="m1", name="")


def test_capability_immutable_and_can():
    c = ModelCapability(id="cap1", owner_id="m1", operations=["chat", "preview"])
    assert c.external_calls == 0
    assert c.can("chat")
    assert not c.can("embedding")
    with pytest.raises(ValueError):
        ModelCapability(id="cap1", owner_id="")


def test_contract_deterministic_hash():
    a = ModelContract(contract_id="c1", owner_id="m1", operations=["chat"])
    b = ModelContract(contract_id="c1", owner_id="m1", operations=["chat"])
    assert a.hash() == b.hash()
    c = ModelContract(contract_id="c1", owner_id="m1", operations=["embedding"])
    assert a.hash() != c.hash()
    assert a.external_calls == 0


def test_metadata_defaults_and_immutable():
    m = ModelMetadata(owner_id="m1")
    assert m.created_at  # auto-filled
    assert m.preview_only is True
    assert m.no_inference is True
    assert m.external_calls == 0
    with pytest.raises(Exception):
        m.owner_id = "other"


def test_registry_register_and_query():
    r = ModelRegistry()
    d = ModelDescriptor(id="m1", name="Chat-1", model_type="chat")
    r.register(d)
    assert r.exists("m1")
    assert r.get("m1") == d
    assert r.get_by_name("Chat-1") == d
    assert r.count() == 1
    assert len(r.all()) == 1
    assert not r.exists("nope")
    assert r.get("nope") is None


def test_registry_capabilities():
    r = ModelRegistry()
    d = ModelDescriptor(id="m1", name="Chat-1", model_type="chat")
    cap = ModelCapability(id="cap1", owner_id="m1", operations=["chat"])
    r.register(d)
    r.attach_capability(cap)
    caps = r.capabilities("m1")
    assert len(caps) == 1
    assert caps[0] == cap


def test_builder_compose():
    b = ModelBuilder()
    d = b.build_descriptor("m2", "Emb-1", model_type="embedding")
    assert d.model_type == "embedding"
    c = b.build_contract("c-m2", "m2", ["preview"])
    assert c.external_calls == 0
    m = b.build_metadata("m2")
    assert m.preview_only is True


def test_foundation_builder_compose():
    f = ModelFoundationBuilder()
    out = f.compose("m3", "Reason-1", model_type="reasoning", operations=["preview"])
    assert out["descriptor"].model_type == "reasoning"
    assert out["contract"].external_calls == 0
    assert out["metadata"].no_inference is True


def test_conversation_bridge_readonly():
    r = ModelRegistry()
    r.register(ModelDescriptor(id="m1", name="Chat-1", model_type="chat"))
    conv = ConversationModelFoundation(r)
    b = conv.bind("conv-1", "m1", role="assistant")
    assert isinstance(b, ConversationModelBinding)
    assert b.external_calls == 0
    assert isinstance(conv.models_for("conv-1"), list)
    assert conv.has_model("m1")
    with pytest.raises(ValueError):
        conv.bind("conv-1", "ghost")


def test_dashboard_bridge_five_cards():
    r = ModelRegistry()
    for i, t in enumerate(["chat", "chat", "embedding", "reasoning", "vision"]):
        r.register(ModelDescriptor(id=f"m{i}", name=f"M{i}", model_type=t))
    dash = DashboardModelFoundation(r)
    cards = dash.cards()
    assert isinstance(cards, list)
    assert all(isinstance(c, DashboardModelCard) for c in cards)
    assert len(cards) == 5
    data = dash.as_dict()
    assert len(data["cards"]) == 5


def test_no_network_imports():
    import inspect, sam.model_runtime.model_descriptor as md
    src = inspect.getsource(md)
    for banned in ("import socket", "import requests", "import httpx",
                   "import asyncio", "threading", "subprocess"):
        assert banned not in src
