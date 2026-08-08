"""Tests for C-Phase 3 (Workstream C4): Execution Operational Intelligence.

Memverifikasi observer Execution menghasilkan observasi operasional Execution
(executions, timeline, analytics) secara read-only, tanpa mengeksekusi/mutasi.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.execution_intelligence import (
    ExecutionAnalytics,
    ExecutionIntelligenceObserver,
    ExecutionIntelligenceReport,
    ExecutionTimeline,
    ExecutionTimelineEntry,
    ExecutionView,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _pub_registry() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="execution",
        health_state="healthy",
        operational_state="ready",
        dashboard_count=5,
        metric_count=1,
        has_preview=True,
        has_metadata=True,
        has_lifecycle=False,
    )))
    return reg


# ── Fake ExecutionRegistry + History (read-only) ──

class _FakeExecution:
    def __init__(self, id, name, operation, mode="preview", provider="generic"):
        self.id = id
        self.name = name
        self.operation = operation
        self.mode = mode
        self.provider = provider
        self.category = "execution"
        self.requires_approval = True
        self.tags = []


class _FakeExecRegistry:
    def __init__(self, items):
        self._items = list(items)
    def all(self):
        return list(self._items)


class _FakeHistoryEntry:
    def __init__(self, entry_id, execution_id, status, provider_id, external_calls):
        self.entry_id = entry_id
        self.execution_id = execution_id
        self.status = status
        self.provider_id = provider_id
        self.external_calls = external_calls


class _FakeHistory:
    def __init__(self, entries):
        self._entries = list(entries)
    def all(self):
        return list(self._entries)


def _registries():
    reg = _FakeExecRegistry([
        _FakeExecution("ex-1", "Summarize", "summarize"),
        _FakeExecution("ex-2", "Transform", "transform", mode="execute"),
    ])
    hist = _FakeHistory([
        _FakeHistoryEntry("h1", "ex-1", "completed", "p1", 3),
        _FakeHistoryEntry("h2", "ex-2", "failed", "p2", 5),
    ])
    return reg, hist


class TestExecutionViews:
    def test_lists_executions(self):
        reg, hist = _registries()
        ob = ExecutionIntelligenceObserver(_pub_registry(), reg, hist)
        exs = ob.executions()
        assert len(exs) == 2
        assert isinstance(exs[0], ExecutionView)
        assert exs[0].execution_id == "ex-1"
        assert exs[1].mode == "execute"

    def test_health_from_publication(self):
        reg, hist = _registries()
        ob = ExecutionIntelligenceObserver(_pub_registry(), reg, hist)
        assert ob.executions()[0].health == "healthy"


class TestExecutionTimeline:
    def test_timeline_entries(self):
        reg, hist = _registries()
        ob = ExecutionIntelligenceObserver(_pub_registry(), reg, hist)
        tl = ob.timeline()
        assert isinstance(tl, ExecutionTimeline)
        assert tl.total == 2
        assert isinstance(tl.entries[0], ExecutionTimelineEntry)
        assert tl.entries[0].status == "completed"


class TestExecutionAnalytics:
    def test_analytics_counts(self):
        reg, hist = _registries()
        ob = ExecutionIntelligenceObserver(_pub_registry(), reg, hist)
        a = ob.analytics()
        assert isinstance(a, ExecutionAnalytics)
        assert a.total == 2
        assert a.completed == 1
        assert a.failed == 1
        assert a.external_calls == 8


class TestExecutionReport:
    def test_report_aggregates(self):
        reg, hist = _registries()
        ob = ExecutionIntelligenceObserver(_pub_registry(), reg, hist)
        rep = ob.report()
        assert isinstance(rep, ExecutionIntelligenceReport)
        assert rep.timeline is not None
        assert rep.analytics is not None
        assert rep.as_dict()["execution_count"] == 2


class TestExecutionReadOnly:
    def test_pub_registry_unchanged(self):
        reg = _pub_registry()
        r, h = _registries()
        before = reg.observe_all().runtime_count
        ob = ExecutionIntelligenceObserver(reg, r, h)
        ob.report(); ob.executions(); ob.timeline(); ob.analytics()
        after = reg.observe_all().runtime_count
        assert before == after == 1
