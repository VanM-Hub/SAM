"""Sprint 247 — Provider Mapping.

Program B — Model Runtime Integration.
Mapping: OpenAI, Anthropic, Gemini, DeepSeek, Ollama. Belum network.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.provider_mapping import ProviderMapping
from sam.model_runtime.provider_selector import ProviderSelector, ProviderSelection
from sam.model_runtime.provider_profile import ProviderProfile
from sam.model_runtime.provider_matrix import ProviderMatrix
from sam.model_runtime.provider_preview import ProviderPreview
from sam.model_runtime.provider_summary import ProviderSummarizer, ProviderSummary
from sam.model_runtime.conversation_mapping import ConversationMapping
from sam.model_runtime.dashboard_mapping import DashboardMapping


def test_provider_mapping_immutable():
    m = ProviderMapping(mapping_id="m1", model_name="gpt-4", provider="openai")
    assert m.external_calls == 0
    with pytest.raises(Exception):
        m.provider = "anthropic"
    assert m.as_dict()["provider"] == "openai"


def test_selector_known_five_providers():
    sel = ProviderSelector()
    for prov in ("openai", "anthropic", "gemini", "deepseek", "ollama"):
        m = ProviderMapping(mapping_id=f"m-{prov}", model_name="x", provider=prov)
        s = sel.select(m)
        assert isinstance(s, ProviderSelection)
        assert s.provider == prov
        assert s.external_calls == 0


def test_selector_fallback():
    sel = ProviderSelector()
    m = ProviderMapping(mapping_id="m1", model_name="x", provider="ghost")
    s = sel.select(m)
    assert s.provider == "openai"  # fallback default
    assert s.reason == "fallback-default"


def test_provider_profile_immutable():
    p = ProviderProfile(provider="anthropic", capabilities=["chat"], default_model="claude")
    assert p.external_calls == 0
    assert p.preview_only is True


def test_provider_matrix():
    p1 = ProviderProfile(provider="openai", capabilities=["chat", "embedding"])
    p2 = ProviderProfile(provider="gemini", capabilities=["chat", "vision"])
    mx = ProviderMatrix(profiles=[p1, p2], rows={
        "chat": ("openai", "gemini"),
        "vision": ("gemini",),
    })
    assert mx.provider("openai") == p1
    assert mx.provider("nope") is None
    assert mx.as_dict()["matrix_id"] == "provider-matrix"


def test_provider_preview():
    m = ProviderMapping(mapping_id="m1", model_name="gpt-4", provider="openai")
    sel = ProviderSelector().select(m)
    pv = ProviderPreview(preview_id="pv1", mapping=m, selection=sel)
    assert "no network call" in pv.note
    assert pv.external_calls == 0


def test_provider_summary():
    mx = ProviderMatrix(profiles=[
        ProviderProfile(provider="openai", capabilities=["chat", "embedding"]),
        ProviderProfile(provider="gemini", capabilities=["chat", "vision"]),
    ])
    summ = ProviderSummarizer().summarize(mx)
    assert isinstance(summ, ProviderSummary)
    assert summ.count == 2
    assert summ.by_capability["chat"] == 2
    assert summ.by_capability["vision"] == 1
    assert summ.external_calls == 0


def test_conversation_mapping_bridge():
    conv = ConversationMapping()
    m = ProviderMapping(mapping_id="m1", model_name="gpt-4", provider="openai")
    out = conv.resolve("conv-1", m)
    assert out.external_calls == 0
    assert out.selection.provider == "openai"


def test_dashboard_mapping_rows():
    dash = DashboardMapping()
    mx = ProviderMatrix(profiles=[ProviderProfile(provider="ollama", capabilities=["chat"])])
    rows = dash.rows(mx)
    assert len(rows) == 1
    assert rows[0].provider == "ollama"
    summ = dash.summary(mx)
    assert summ.count == 1
    assert summ.external_calls == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.provider_selector as ps
    src = inspect.getsource(ps)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
