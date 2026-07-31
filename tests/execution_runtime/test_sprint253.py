"""Sprint 253 - Provider Dispatcher.

Program C - Real Execution Runtime.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.provider_dispatcher import (
    ProviderDispatcher, DispatchTarget, KNOWN_PROVIDERS,
)
from sam.execution_runtime.provider_selector import ProviderSelector, SelectorRanking
from sam.execution_runtime.provider_history import (
    ProviderHistory, ProviderHistoryEntry,
)
from sam.execution_runtime.provider_summary import (
    ProviderSummary, ProviderSummaryData,
)
from sam.execution_runtime.provider_pipeline import ProviderPipeline, ProviderPipelineResult


def test_known_providers_ten():
    assert len(KNOWN_PROVIDERS) == 10
    expected = {"filesystem", "shell", "sqlite", "docker", "openclaw",
                "openai", "anthropic", "gemini", "deepseek", "ollama"}
    assert set(KNOWN_PROVIDERS) == expected


def test_dispatcher_known():
    d = ProviderDispatcher()
    for p in KNOWN_PROVIDERS:
        assert d.is_known(p) is True
    assert d.is_known("unknown") is False


def test_dispatcher_dispatch():
    d = ProviderDispatcher()
    d.register("openai", object())
    target = d.dispatch(ExecutionRequest("e1", "openai", "chat", mode="execute", approved=True))
    assert isinstance(target, DispatchTarget)
    assert target.provider_id == "openai"
    assert target.operation == "chat"
    assert target.available is True
    assert target.external_calls == 0  # dispatch tidak mengeksekusi


def test_dispatcher_unknown_raises():
    d = ProviderDispatcher()
    with pytest.raises(ValueError):
        d.dispatch(ExecutionRequest("e1", "ghost", "x"))


def test_dispatcher_unavailable_when_not_registered():
    d = ProviderDispatcher()
    t = d.dispatch(ExecutionRequest("e1", "openai", "chat"))
    assert t.available is False


def test_dispatch_immutable():
    t = DispatchTarget(provider_id="openai", operation="chat")
    with pytest.raises(Exception):
        t.provider_id = "ollama"


def test_selector_best_explicit():
    req = ExecutionRequest("e1", "anthropic", "chat")
    best = ProviderSelector().best(req)
    assert isinstance(best, SelectorRanking)
    assert best.provider_id == "anthropic"
    assert best.score == 10.0


def test_selector_rank_deterministic():
    req = ExecutionRequest("e1", "gemini", "chat")
    r1 = ProviderSelector().rank(req)
    r2 = ProviderSelector().rank(req)
    assert [x.provider_id for x in r1] == [x.provider_id for x in r2]


def test_selector_no_provider_specific_logic():
    # best tanpa preference => deterministik berdasarkan urutan candidates
    req = ExecutionRequest("e1", "x-not-in-list", "chat")
    best = ProviderSelector().best(req)
    assert best.provider_id == KNOWN_PROVIDERS[0]


def test_history_record():
    h = ProviderHistory()
    e = h.record(DispatchTarget(provider_id="openai", operation="chat"))
    assert isinstance(e, ProviderHistoryEntry)
    assert e.entry_id == "ph-1"
    assert h.count() == 1
    assert h.count_by_provider("openai") == 1


def test_history_append_only():
    h = ProviderHistory()
    h.record(DispatchTarget("sqlite", "query"))
    h.record(DispatchTarget("openai", "chat"))
    assert h.count() == 2
    assert h.count_by_provider("sqlite") == 1
    assert h.count_by_provider("openai") == 1


def test_history_all_returns_copy():
    h = ProviderHistory()
    h.record(DispatchTarget("openai", "chat"))
    lst = h.all()
    lst.clear()
    assert h.count() == 1


def test_summary_groups():
    entries = [
        ProviderHistoryEntry("1", "openai", "chat", external_calls=0),
        ProviderHistoryEntry("2", "openai", "chat", external_calls=0),
        ProviderHistoryEntry("3", "sqlite", "query", external_calls=0),
    ]
    s = ProviderSummary().summarize(entries)
    assert isinstance(s[0], ProviderSummaryData)
    by_id = {x.provider_id: x for x in s}
    assert by_id["openai"].dispatches == 2
    assert by_id["sqlite"].dispatches == 1
    assert by_id["openai"].external_calls == 0


def test_pipeline_run():
    pl = ProviderPipeline()
    req = ExecutionRequest("e1", "openai", "chat", mode="execute", approved=True, approver="v")
    res = pl.run("pp1", req)
    assert isinstance(res, ProviderPipelineResult)
    assert res.execution_id == "e1"
    assert res.target.provider_id == "openai"
    assert len(res.ranking) == 10
    assert res.external_calls == 0
    assert res.history.entry_id == "ph-1"


def test_pipeline_dispatch_via_interface():
    # dispatcher menolak provider tak dikenal => pipeline gagal
    pl = ProviderPipeline()
    with pytest.raises(ValueError):
        pl.run("pp1", ExecutionRequest("e1", "ghost", "x"))


def test_pipeline_no_execution_on_dispatch():
    # dispatch HANYA routing; tidak pernah memanggil provider
    pl = ProviderPipeline()
    req = ExecutionRequest("e1", "openai", "chat", mode="execute", approved=False)
    res = pl.run("pp1", req)
    assert res.external_calls == 0
    assert res.history.external_calls == 0


def test_all_ten_providers_registerable():
    d = ProviderDispatcher()
    for p in KNOWN_PROVIDERS:
        d.register(p, object())
        assert d.dispatch(ExecutionRequest(f"e-{p}", p, "op")).available is True


def test_no_forbidden_imports_dispatcher():
    import inspect
    import sam.execution_runtime.provider_dispatcher as pd
    src = inspect.getsource(pd)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
